"""
National_welfare_data_detail.json(복지로 중앙부처 복지서비스, servId별 목록+상세 병합)을
온통청년 policy 테이블 컬럼 형식으로 매핑해서 DB에 적재하는 스크립트.

import_welfare_policies.py(지자체용)와 같은 구조이지만, 중앙부처 상세조회 API는 지자체와
필드 이름/구조가 달라서(예: wlfareInfoDtlCd -> servSeCode, wlfareInfoReldCn -> servSeDetailLink
등) 매핑 로직을 따로 뒀다.

매핑 원칙(자세한 값은 transform_record 참고):
    plcyNo         = "BOKJIRO-NATL-" + servId  (지자체 import와 접두어를 다르게 해서 충돌 방지)
    source         = "BOKJIRO"  (지자체와 동일 - 관리자 화면엔 어차피 "복지로"로만 구분하면 충분)
    plcyNm         = servNm
    plcyExplnCn    = wlfareInfoOutlCn (없으면 목록의 servDgst)
    plcySprtCn     = alwServCn
    rgtrInstCdNm   = jurMnofNm (부처+담당부서가 이미 합쳐진 문자열, 예: "국토교통부 주택공급정책과")
    sprvsnInstCdNm = jurOrgNm (담당부서명만, 예: "주택공급정책과" - summary에만 있고 detail엔 없음)
    plcyAplyMthdCn = applmetList 중 "신청기관연락처목록" 단계의 안내 텍스트
    srngMthdCn / addAplyQlfcCndCn = slctCritCn (선정기준)
    ptcpPrpTrgtCn / earnEtcCn     = tgtrDtlCn (지원대상 상세 - 지자체 API에 없던 필드라 여기선
                                     sprtTrgtCn 대신 이걸 씀. 소득 조건이 이 텍스트 안에 섞여
                                     있는 경우가 많아 earnEtcCn에도 재사용)
    sprtTrgtMinAge/MaxAge = age_resolver.resolve_age() 참고. 본문(tgtrDtlCn)에서 정확한 나이
    범위를 뽑을 수 있으면 그 값을, 못 뽑으면 lifeArray(생애주기) 기반값을 쓴다. 전연령은 (0, 0)
    으로 통일(sprtTrgtAgeLmtYn은 원본 오류가 많아 더 이상 채우지 않고 NULL로 둠).
    sbizCd = sbiz_resolver.resolve_sbiz() 참고. trgterIndvdlArray(장애인/한부모·조손 등)와
    lifeArray(임신·출산->여성)를 기존 ONTONG 코드(SBIZ_MAP)와 매핑되는 것만 채운다.
    지역(policy_region) = 전국 매핑. 중앙부처 사업은 시도명(ctpvNm) 자체가 응답에 없어서 지자체
    임포트처럼 시도명 기준으로 매핑할 근거 데이터는 없지만, 중앙부처 사업은 성격상 전국 대상인
    경우가 대부분이고 온통청년 데이터의 기존 "전국 단위 정책"도 zipcd 테이블의 모든
    시군구코드를 policy_region에 연결하는 방식으로 처리돼 있어서, 같은 방식을 따른다
    (어떤 지역으로 필터링해도 노출됨). zipcd 테이블이 비어있으면 지역 매핑은 건너뛴다.

사전 준비:
    pip install pymysql python-dotenv
    (.env는 기존 스크립트들과 동일한 DB_* 값 사용)
    source 컬럼이 DB에 아직 없다면 먼저 추가(지자체 import 때 이미 추가했다면 생략):
        ALTER TABLE policy ADD COLUMN source VARCHAR(20) NULL AFTER plcySprtCn;

사용법:
    python import_national_welfare_policies.py --peek
        # 1건만 변환해서 어떤 값이 들어가는지 미리보기 (DB 저장 안 함)

    python import_national_welfare_policies.py
        # National_welfare_data_detail.json 전체를 policy 테이블에 적재 + 전국 지역 매핑까지

    python import_national_welfare_policies.py --skip-region
        # policy_region 매핑 없이 policy 테이블만 적재하고 싶을 때
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime

import pymysql
from dotenv import load_dotenv

from age_resolver import resolve_age
from sbiz_resolver import resolve_sbiz

load_dotenv()

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", 3306)),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME"),
    "charset": "utf8mb4",
}

DETAIL_FILE = "National_welfare_data_detail.json"
PLCYNO_PREFIX = "BOKJIRO-NATL-"

# policy 테이블 컬럼 순서 (auto_increment인 policy_id, createdAt/updatedAt DEFAULT 제외)
COLUMNS = [
    "plcyNo", "plcyNm", "plcyKywdNm", "plcyExplnCn", "lclsfNm", "mclsfNm",
    "plcySprtCn", "source", "rgtrInstCdNm", "sprvsnInstCdNm", "sprvsnInstPicNm", "operInstCdNm", "operInstPicNm",
    "bizPrdBgngYmd", "bizPrdEndYmd", "bizPrdEtcCn", "plcyAplyMthdCn", "srngMthdCn", "aplyUrlAddr",
    "sbmsnDcmntCn", "aplyYmd", "refUrlAddr1", "refUrlAddr2", "etcMttrCn",
    "sprtSclCnt", "sprtTrgtMinAge", "sprtTrgtMaxAge", "sprtTrgtAgeLmtYn", "earnMinAmt", "earnMaxAmt",
    "earnEtcCn", "earnCndSeCd", "addAplyQlfcCndCn", "ptcpPrpTrgtCn", "mrgSttsCd", "sbizCd",
    "inqCnt", "frstRegDt", "lastMdfcnDt",
]

_PHONE_RE = re.compile(r"^[0-9][0-9\-]*$")


def as_list(val):
    """xmltodict는 같은 태그가 1개면 dict, 여러 개면 list를 반환해서 방어적으로 통일."""
    if val is None:
        return []
    if isinstance(val, list):
        return val
    return [val]


def clean(val):
    """값을 문자열로 바꾸고 공백을 지운다. 비어있으면 None."""
    if val is None:
        return None
    val = str(val).strip()
    return val if val else None


def parse_int(val):
    """값을 정수로 변환한다. 실패하면 None."""
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None


def parse_ymd(val):
    """"YYYYMMDD" 문자열을 datetime으로 변환한다. 실패하면 None."""
    val = clean(val)
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y%m%d")
    except ValueError:
        return None


def looks_like_url(text: str) -> bool:
    """전화번호가 아니면서 URL처럼 생긴 문자열인지 확인한다."""
    if not text or " " in text:
        return False
    if text.startswith("http://") or text.startswith("https://"):
        return True
    if _PHONE_RE.match(text):
        return False
    return "." in text


def normalize_url(text: str) -> str:
    """URL에 스키마(https://)가 없으면 붙여준다."""
    if text.startswith("http://") or text.startswith("https://"):
        return text
    return "https://" + text


def build_apply_period(detail: dict) -> str:
    """신청기간(aplyYmd) 문자열을 만든다: 수시모집이면 "상시(수시)", 기간이 있으면 범위,
    없으면 지원주기명 또는 "상시"."""
    cyc = clean(detail.get("sprtCycNm"))
    bgn = clean(detail.get("enfcBgngYmd"))
    end = clean(detail.get("enfcEndYmd"))
    if cyc and "수시" in cyc:
        return "상시(수시)"
    if bgn and end:
        return f"{bgn} ~ {end}"
    return cyc or "상시"


def build_apply_method(detail: dict):
    """신청방법(plcyAplyMthdCn) 텍스트를 만든다. "신청" 단계의 링크가 있으면 그것만,
    없으면 모든 단계를 "[단계명] 링크" 형태로 나열한다."""
    items = [i for i in as_list(detail.get("applmetList")) if isinstance(i, dict)]
    apply_stage = []
    for i in items:
        nm = clean(i.get("servSeDetailNm"))
        link = clean(i.get("servSeDetailLink"))
        if nm and "신청" in nm and link:
            apply_stage.append(link)
    if apply_stage:
        return "\n".join(dict.fromkeys(apply_stage))  # 순서 유지하며 중복 제거

    lines = []
    for i in items:
        nm = clean(i.get("servSeDetailNm"))
        link = clean(i.get("servSeDetailLink"))
        if nm or link:
            lines.append(f"[{nm or ''}] {link or ''}".strip())
    return "\n".join(lines) if lines else None


def build_apply_url(detail: dict):
    """신청 URL 목록에서 URL처럼 생긴 첫 번째 링크를 찾아 스키마를 붙여 반환한다."""
    for item in as_list(detail.get("inqplHmpgReldList")):
        if not isinstance(item, dict):
            continue
        link = clean(item.get("servSeDetailLink"))
        if link and looks_like_url(link):
            return normalize_url(link)
    return None


def build_submission_docs(detail: dict) -> str:
    """제출서류 목록(basfrmList)을 줄바꿈으로 나열한 텍스트로 만든다."""
    lines = []
    for item in as_list(detail.get("basfrmList")):
        if not isinstance(item, dict):
            continue
        name = clean(item.get("servSeDetailNm"))
        url = clean(item.get("servSeDetailLink"))
        if name or url:
            lines.append(f"- {name or ''} {url or ''}".strip())
    return "\n".join(lines) if lines else "제출 서류 없음 (복지로 원문 확인 필요)"


def build_etc_matter(detail: dict):
    """근거법령/문의처/기준연도 정보를 합쳐 기타사항(etcMttrCn) 텍스트로 만든다."""
    lines = []
    laws = [clean(i.get("servSeDetailNm")) for i in as_list(detail.get("baslawList")) if isinstance(i, dict)]
    laws = [l for l in laws if l]
    if laws:
        lines.append("[근거법령] " + ", ".join(laws))

    contacts = []
    for item in as_list(detail.get("inqplCtadrList")):
        if not isinstance(item, dict):
            continue
        nm = clean(item.get("servSeDetailNm"))
        cn = clean(item.get("servSeDetailLink"))
        if nm or cn:
            contacts.append(f"{nm or ''} {cn or ''}".strip())
    if contacts:
        lines.append("[문의처] " + " / ".join(contacts))

    crtr_yr = clean(detail.get("crtrYr"))
    if crtr_yr:
        lines.append(f"[기준연도] {crtr_yr}")

    return "\n".join(lines) if lines else None


def build_keyword(detail: dict) -> str:
    """정책 키워드(plcyKywdNm)를 관심주제 또는 생애주기명에서 뽑는다. 둘 다 없으면 "청년"."""
    return clean(detail.get("intrsThemaArray")) or clean(detail.get("lifeArray")) or "청년"


def build_mclsf(detail: dict) -> str:
    """관심주제(intrsThemaArray)를 원본 그대로 저장한다(여러 개면 콤마 그대로 유지).
    ONTONG도 mclsfNm에 콤마로 여러 값을 넣는 경우가 있어 같은 규칙이고, 화면에 보여줄 대표
    카테고리를 뽑는 건 recommendation_service.py가 이 원본 값을 보고 별도로 판단한다
    (여기서 첫 값만 남기고 잘라버리면 DB에 원문 분류가 안 남아서 복원이 안 됨)."""
    return clean(detail.get("intrsThemaArray")) or "기타"


def transform_record(record: dict) -> tuple:
    """복지로 중앙부처 원본 레코드(목록+상세) 하나를 policy 테이블 COLUMNS 순서의 튜플로 변환한다."""
    serv_id = record["servId"]
    summary = record.get("summary") or {}
    detail = record.get("detail") or {}

    tgtr_cn = clean(detail.get("tgtrDtlCn"))
    slct_cn = clean(detail.get("slctCritCn"))
    min_age, max_age = resolve_age(detail.get("lifeArray"), tgtr_cn)
    sbiz_cd = resolve_sbiz(
        detail.get("trgterIndvdlArray"), detail.get("lifeArray"),
        detail.get("servNm"), tgtr_cn, slct_cn,
    )

    values = {
        "plcyNo": PLCYNO_PREFIX + serv_id,
        "plcyNm": clean(detail.get("servNm")) or clean(summary.get("servNm")) or "(제목 없음)",
        "plcyKywdNm": build_keyword(detail),
        "plcyExplnCn": clean(detail.get("wlfareInfoOutlCn")) or clean(summary.get("servDgst")) or "-",
        "lclsfNm": "복지",
        "mclsfNm": build_mclsf(detail),
        "plcySprtCn": clean(detail.get("alwServCn")) or "-",
        "source": "BOKJIRO",
        "rgtrInstCdNm": clean(detail.get("jurMnofNm")) or clean(summary.get("jurMnofNm")),
        "sprvsnInstCdNm": clean(summary.get("jurOrgNm")) or clean(detail.get("jurOrgNm")),
        "sprvsnInstPicNm": None,
        "operInstCdNm": None,
        "operInstPicNm": None,
        "bizPrdBgngYmd": None,
        "bizPrdEndYmd": None,
        "bizPrdEtcCn": clean(detail.get("sprtCycNm")),
        "plcyAplyMthdCn": build_apply_method(detail),
        "srngMthdCn": slct_cn,
        "aplyUrlAddr": build_apply_url(detail),
        "sbmsnDcmntCn": build_submission_docs(detail),
        "aplyYmd": build_apply_period(detail),
        "refUrlAddr1": clean(summary.get("servDtlLink")),
        "refUrlAddr2": None,
        "etcMttrCn": build_etc_matter(detail),
        "sprtSclCnt": None,
        "sprtTrgtMinAge": min_age,
        "sprtTrgtMaxAge": max_age,
        "sprtTrgtAgeLmtYn": None,
        "earnMinAmt": None,
        "earnMaxAmt": None,
        "earnEtcCn": tgtr_cn or "-",
        "earnCndSeCd": None,
        "addAplyQlfcCndCn": slct_cn or "-",
        "ptcpPrpTrgtCn": tgtr_cn or "-",
        "mrgSttsCd": None,
        "sbizCd": sbiz_cd,
        "inqCnt": parse_int(summary.get("inqNum")) or 0,
        "frstRegDt": parse_ymd(summary.get("svcfrstRegTs")),
        "lastMdfcnDt": None,
    }
    return tuple(values[c] for c in COLUMNS)


def load_records() -> list:
    """상세정보 파일을 읽어, servId와 detail이 둘 다 있는 레코드만 반환한다."""
    with open(DETAIL_FILE, "r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        sys.exit(f"{DETAIL_FILE}가 리스트 형태가 아닙니다.")
    records = [r for r in data if r.get("servId") and r.get("detail")]
    skipped = len(data) - len(records)
    if skipped:
        print(f"[정보] servId 또는 detail이 없는 {skipped}건은 건너뜁니다.")
    return records


def insert_batch(conn, rows: list):
    """정책 배치를 삽입한다. plcyNo가 이미 있으면 나머지 컬럼을 최신 값으로 덮어쓴다(upsert)."""
    if not rows:
        return
    col_list = ", ".join(f"`{c}`" for c in COLUMNS)
    placeholders = ", ".join(["%s"] * len(COLUMNS))
    update_clause = ", ".join(f"`{c}`=VALUES(`{c}`)" for c in COLUMNS if c != "plcyNo")
    sql = f"""
        INSERT INTO policy ({col_list})
        VALUES ({placeholders})
        ON DUPLICATE KEY UPDATE {update_clause}
    """
    with conn.cursor() as cur:
        cur.executemany(sql, rows)
    conn.commit()


def load_zipcd_mapping(conn) -> list:
    """전국 매핑용 - [(시군구코드, 지역명), ...] 전체를 zipcd 테이블(load_zipcd_mapping.py로
    zipcd_mapping.csv를 적재해둔 것)에서 그대로 반환. 예전엔 ai/data/zipcd_mapping.csv를
    상대경로로 읽었는데, 디렉터리 구조가 바뀌면 깨지는 경로 의존이라 DB로 옮겼다."""
    with conn.cursor() as cur:
        cur.execute("SELECT sigungu_code, full_name FROM zipcd")
        rows = cur.fetchall()
    if not rows:
        print("[경고] zipcd 테이블이 비어있어 지역 매핑을 건너뜁니다 (load_zipcd_mapping.py 먼저 실행 필요).")
    return [(code, name) for code, name in rows]


def build_plcyno_to_id_map(conn) -> dict:
    """이 스크립트로 적재된(plcyNo가 "BOKJIRO-NATL-"로 시작하는) 정책들의 plcyNo -> policy_id 매핑을 만든다."""
    with conn.cursor() as cur:
        cur.execute("SELECT policy_id, plcyNo FROM policy WHERE plcyNo LIKE %s", (f"{PLCYNO_PREFIX}%",))
        rows = cur.fetchall()
    return {plcy_no: policy_id for policy_id, plcy_no in rows}


def insert_region_pairs(conn, pairs: list, batch_size: int = 1000) -> int:
    """(policy_id, zip_code) 쌍들을 policy_region 테이블에 배치로 삽입한다(중복은 무시)."""
    if not pairs:
        return 0
    sql = "INSERT IGNORE INTO policy_region (policy_id, zip_code) VALUES (%s, %s)"
    total = 0
    with conn.cursor() as cur:
        for i in range(0, len(pairs), batch_size):
            chunk = pairs[i:i + batch_size]
            cur.executemany(sql, chunk)
            total += len(chunk)
    conn.commit()
    return total


def run_region_mapping(conn, records: list):
    """중앙부처 사업은 시도명(ctpvNm)이 없어 개별 매칭이 불가능하므로, 전국 정책 취급으로
    zipcd_mapping.csv의 모든 시군구코드를 각 정책에 연결한다(온통청년 기존 전국 단위 정책과
    동일한 방식). 어떤 지역으로 필터링해도 노출된다."""
    mapping = load_zipcd_mapping(conn)
    if not mapping:
        return
    all_codes = [code for code, _ in mapping]

    plcyno_map = build_plcyno_to_id_map(conn)

    pairs = []
    for record in records:
        serv_id = record["servId"]
        plcy_no = PLCYNO_PREFIX + serv_id
        policy_id = plcyno_map.get(plcy_no)
        if policy_id is None:
            continue
        pairs.extend((policy_id, code) for code in all_codes)

    inserted = insert_region_pairs(conn, pairs)
    print(f"policy_region: {inserted}건 적재 시도 (전국 매핑, 시군구코드 {len(all_codes)}개 x 정책 {len(plcyno_map)}건)")


def main():
    """상세정보 파일 전체를 policy 테이블 형식으로 변환해 upsert하고, 전국 지역 매핑까지 갱신한다."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--peek", action="store_true", help="1건만 변환 결과 미리보기 (DB 저장 안 함)")
    parser.add_argument("--skip-region", action="store_true", help="policy_region 매핑 생략")
    args = parser.parse_args()

    records = load_records()
    print(f"{DETAIL_FILE}에서 상세정보 있는 {len(records)}건 로드")
    print(f"TOTAL_COUNT:{len(records)}")  # external_sync.py가 파싱해 관리자 화면에 작업량으로 표시

    if args.peek:
        row = transform_record(records[0])
        preview = dict(zip(COLUMNS, row))
        print(json.dumps(preview, ensure_ascii=False, indent=2, default=str))
        return

    conn = pymysql.connect(**DB_CONFIG)
    print(f"DB 연결 성공: {DB_CONFIG['host']}/{DB_CONFIG['database']}")

    try:
        rows = [transform_record(r) for r in records]
        insert_batch(conn, rows)
        print(f"policy 테이블 적재/업데이트 완료: {len(rows)}건")

        if not args.skip_region:
            run_region_mapping(conn, records)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
