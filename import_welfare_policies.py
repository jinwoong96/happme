"""
welfare_data_detail.json(복지로 지자체 복지서비스, servId별 목록+상세 병합)을
온통청년 policy 테이블 컬럼 형식으로 매핑해서 DB에 적재하는 스크립트.

welfare_data_detail.json은 fetch_welfare_detail.py로 만든 파일이며,
각 항목은 {"servId": ..., "summary": {...목록 API 필드...}, "detail": {...상세 API(wantedDtl) 필드...}} 형태.

매핑 원칙 (자세한 값은 transform_record 참고):
    plcyNo         = "BOKJIRO-" + servId  (온통청년 plcyNo와 충돌 방지)
    source         = "BOKJIRO"
    plcyNm         = servNm
    plcyExplnCn    = servDgst
    plcySprtCn     = alwServCn
    rgtrInstCdNm   = bizChrDeptNm (전체 문자열, 예: "경기도 파주시 복지정책국 여성가족과")
    sprvsnInstCdNm = bizChrDeptNm에서 "{ctpvNm} {sggNm}" 지역 접두어를 뗀 부서명만
                     (예: "복지정책국 여성가족과". 접두어가 안 맞는 소수 케이스는 원문 그대로 사용)
    plcyAplyMthdCn = aplyMtdCn (없으면 aplyMtdNm)
    srngMthdCn / addAplyQlfcCndCn = slctCritCn (선정기준)
    ptcpPrpTrgtCn / earnEtcCn     = sprtTrgtCn (복지로엔 소득조건이 따로 없어 지원대상 원문 재사용)
    sprtTrgtMinAge/MaxAge = age_resolver.resolve_age() 참고. 본문(sprtTrgtCn)에서 정확한 나이
    범위를 뽑을 수 있으면 그 값을, 못 뽑으면 lifeNmArray(생애주기) 기반값을 쓴다. 전연령은 (0, 0)
    으로 통일(sprtTrgtAgeLmtYn은 원본 오류가 많아 더 이상 채우지 않고 NULL로 둠).
    sbizCd = sbiz_resolver.resolve_sbiz() 참고. trgterIndvdlNmArray(장애인/한부모·조손 등)와
    lifeNmArray(임신·출산->여성)를 기존 ONTONG 코드(SBIZ_MAP)와 매핑되는 것만 채운다.
    지역(ctpvNm+sggNm) -> policy_region.zip_code는 zipcd 테이블(load_zipcd_mapping.py로 적재)로 매칭
    (예: ctpvNm="경기도", sggNm="파주시" -> sido_name="경기도" & sigungu_name="파주시"인 시군구코드로 매핑.
     sggNm이 비어있으면(광역 단위 정책) ctpvNm과 sido_name이 일치하는 시군구코드 전부를 매핑)

사전 준비:
    pip install pymysql python-dotenv
    (.env는 기존 import_policies.py와 동일한 DB_* 값 사용)

    source 컬럼이 DB에 아직 없다면 먼저 추가:
        ALTER TABLE policy ADD COLUMN source VARCHAR(20) NULL AFTER plcySprtCn;

사용법:
    python import_welfare_policies.py --peek
        # 1건만 변환해서 어떤 값이 들어가는지 미리보기 (DB 저장 안 함)

    python import_welfare_policies.py
        # welfare_data_detail.json 전체를 policy 테이블에 적재 + policy_region 매핑까지

    python import_welfare_policies.py --skip-region
        # policy_region 매핑 없이 policy 테이블만 적재하고 싶을 때
"""

import os
import sys
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

DETAIL_FILE = "welfare_data_detail.json"
PLCYNO_PREFIX = "BOKJIRO-"

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


def build_submission_docs(detail: dict) -> str:
    """제출서류 목록(basfrmList)을 줄바꿈으로 나열한 텍스트로 만든다."""
    lines = []
    for item in as_list(detail.get("basfrmList")):
        if not isinstance(item, dict):
            continue
        name = clean(item.get("wlfareInfoReldNm"))
        url = clean(item.get("wlfareInfoReldCn"))
        if name and "첨부파일없음" in name and not url:
            continue
        if name or url:
            lines.append(f"- {name or ''} {url or ''}".strip())
    return "\n".join(lines) if lines else "제출 서류 없음 (복지로 원문 확인 필요)"


def build_etc_matter(detail: dict):
    """근거법령/문의처 정보를 합쳐 기타사항(etcMttrCn) 텍스트로 만든다."""
    lines = []
    laws = [clean(i.get("wlfareInfoReldNm")) for i in as_list(detail.get("baslawList")) if isinstance(i, dict)]
    laws = [l for l in laws if l]
    if laws:
        lines.append("[근거법령] " + ", ".join(laws))

    contacts = []
    for item in as_list(detail.get("inqplCtadrList")):
        if not isinstance(item, dict):
            continue
        nm = clean(item.get("wlfareInfoReldNm"))
        cn = clean(item.get("wlfareInfoReldCn"))
        if nm or cn:
            contacts.append(f"{nm or ''} {cn or ''}".strip())
    if contacts:
        lines.append("[문의처] " + " / ".join(contacts))

    return "\n".join(lines) if lines else None


def build_apply_url(detail: dict):
    """신청 URL 목록에서 http로 시작하는 첫 번째 링크를 찾는다."""
    for item in as_list(detail.get("inqplHmpgReldList")):
        if not isinstance(item, dict):
            continue
        url = clean(item.get("wlfareInfoReldCn"))
        if url and url.startswith("http"):
            return url
    return None


def build_sprvsn_dept(detail: dict) -> str:
    """bizChrDeptNm은 "{시도} {시군구} {부서명}" 형태로 지역명이 앞에 붙어있어서(예: "경기도
    파주시 복지정책국 여성가족과"), rgtrInstCdNm에 쓰는 전체 문자열과 별개로 부서명만 뽑아
    sprvsnInstCdNm에 쓴다. 접두어가 어긋나는 소수 케이스(도 이름 개편 등)는 통째로 반환한다."""
    dept = clean(detail.get("bizChrDeptNm"))
    if not dept:
        return None
    ctpv = clean(detail.get("ctpvNm")) or ""
    sgg = clean(detail.get("sggNm")) or ""
    for prefix in (f"{ctpv} {sgg}".strip(), ctpv):
        if prefix and dept.startswith(prefix):
            rest = dept[len(prefix):].strip()
            if rest:
                return rest
    return dept


def build_keyword(detail: dict) -> str:
    """정책 키워드(plcyKywdNm)를 관심주제 또는 생애주기명에서 뽑는다. 둘 다 없으면 "청년"."""
    return clean(detail.get("intrsThemaNmArray")) or clean(detail.get("lifeNmArray")) or "청년"


def build_mclsf(detail: dict) -> str:
    """관심주제(intrsThemaNmArray)를 원본 그대로 저장한다(여러 개면 콤마 그대로 유지).
    ONTONG도 mclsfNm에 콤마로 여러 값을 넣는 경우가 있어 같은 규칙이고, 화면에 보여줄 대표
    카테고리를 뽑는 건 recommendation_service.py가 이 원본 값을 보고 별도로 판단한다
    (여기서 첫 값만 남기고 잘라버리면 DB에 원문 분류가 안 남아서 복원이 안 됨)."""
    return clean(detail.get("intrsThemaNmArray")) or "기타"


def transform_record(record: dict) -> tuple:
    """복지로 원본 레코드(목록+상세) 하나를 policy 테이블 COLUMNS 순서의 튜플로 변환한다."""
    serv_id = record["servId"]
    summary = record.get("summary") or {}
    detail = record.get("detail") or {}

    trgt_cn = clean(detail.get("sprtTrgtCn"))
    slct_cn = clean(detail.get("slctCritCn"))
    apply_url = build_apply_url(detail)
    min_age, max_age = resolve_age(detail.get("lifeNmArray"), trgt_cn)
    sbiz_cd = resolve_sbiz(
        detail.get("trgterIndvdlNmArray"), detail.get("lifeNmArray"),
        detail.get("servNm"), trgt_cn, slct_cn,
    )

    values = {
        "plcyNo": PLCYNO_PREFIX + serv_id,
        "plcyNm": clean(detail.get("servNm")) or clean(summary.get("servNm")) or "(제목 없음)",
        "plcyKywdNm": build_keyword(detail),
        "plcyExplnCn": clean(detail.get("servDgst")) or clean(summary.get("servDgst")) or "-",
        "lclsfNm": "복지",
        "mclsfNm": build_mclsf(detail),
        "plcySprtCn": clean(detail.get("alwServCn")) or "-",
        "source": "BOKJIRO",
        "rgtrInstCdNm": clean(detail.get("bizChrDeptNm")) or clean(summary.get("bizChrDeptNm")),
        "sprvsnInstCdNm": build_sprvsn_dept(detail),
        "sprvsnInstPicNm": None,
        "operInstCdNm": None,
        "operInstPicNm": None,
        "bizPrdBgngYmd": clean(detail.get("enfcBgngYmd")),
        "bizPrdEndYmd": clean(detail.get("enfcEndYmd")),
        "bizPrdEtcCn": clean(detail.get("sprtCycNm")),
        "plcyAplyMthdCn": clean(detail.get("aplyMtdCn")) or clean(detail.get("aplyMtdNm")),
        "srngMthdCn": slct_cn,
        "aplyUrlAddr": apply_url,
        "sbmsnDcmntCn": build_submission_docs(detail),
        "aplyYmd": build_apply_period(detail),
        "refUrlAddr1": clean(summary.get("servDtlLink")) or apply_url,
        "refUrlAddr2": None,
        "etcMttrCn": build_etc_matter(detail),
        "sprtSclCnt": None,
        "sprtTrgtMinAge": min_age,
        "sprtTrgtMaxAge": max_age,
        "sprtTrgtAgeLmtYn": None,
        "earnMinAmt": None,
        "earnMaxAmt": None,
        "earnEtcCn": trgt_cn or "-",
        "earnCndSeCd": None,
        "addAplyQlfcCndCn": slct_cn or "-",
        "ptcpPrpTrgtCn": trgt_cn or "-",
        "mrgSttsCd": None,
        "sbizCd": sbiz_cd,
        "inqCnt": parse_int(detail.get("inqNum")) or 0,
        "frstRegDt": None,
        "lastMdfcnDt": parse_ymd(detail.get("lastModYmd")),
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
    """[(시군구코드, 시도명, 시군구명), ...] - zipcd 테이블(load_zipcd_mapping.py로
    zipcd_mapping.csv를 적재해둔 것)에서 조회한다. 예전엔 ai/data/zipcd_mapping.csv를
    상대경로로 읽었는데, 그 경로가 디렉터리 구조가 바뀌면 깨지는 데다 서비스 간 파일
    의존이라 DB로 옮겼다."""
    with conn.cursor() as cur:
        cur.execute("SELECT sigungu_code, sido_name, sigungu_name FROM zipcd")
        rows = cur.fetchall()
    if not rows:
        print("[경고] zipcd 테이블이 비어있어 지역 매핑을 건너뜁니다 (load_zipcd_mapping.py 먼저 실행 필요).")
    return [(code, sido, sigungu) for code, sido, sigungu in rows]


def zip_codes_for_region(ctpv_nm: str, sgg_nm: str, mapping: list) -> list:
    """ctpvNm(시도)+sggNm(시군구)로 zipcd 테이블을 매칭한다.
    sggNm이 있으면 해당 시군구만, 없으면(광역 단위 정책) 그 시도 전체 시군구코드를 반환한다.
    sggNm이 있는데 zipcd 테이블과 정확히 안 맞으면(예: "세종시" vs "세종특별자치시") 접두 매칭으로
    재시도하고, 그래도 없으면 시도 전체로 넓혀서(과거 동작과 동일) 최소한 매핑이 비지 않게 한다."""
    ctpv_nm = (ctpv_nm or "").strip()
    sgg_nm = (sgg_nm or "").strip()
    if not ctpv_nm:
        return []

    province_rows = [(code, sigungu) for code, sido, sigungu in mapping if sido.startswith(ctpv_nm)]
    if not sgg_nm:
        return [code for code, _ in province_rows]

    exact = [code for code, sigungu in province_rows if sigungu == sgg_nm]
    if exact:
        return exact

    prefix = [code for code, sigungu in province_rows if sigungu.startswith(sgg_nm) or sgg_nm.startswith(sigungu)]
    if prefix:
        return prefix

    return [code for code, _ in province_rows]


def build_plcyno_to_id_map(conn) -> dict:
    """이 스크립트로 적재된(plcyNo가 "BOKJIRO-"로 시작하는) 정책들의 plcyNo -> policy_id 매핑을 만든다."""
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


def delete_region_pairs(conn, policy_ids: list) -> int:
    """재실행 시 옛 매칭 로직(ctpvNm만으로 시도 전체 매핑)으로 잘못 넣은 policy_region 행이
    남지 않도록, 이번에 다시 계산할 policy_id들의 기존 행을 지우고 새로 넣는다."""
    if not policy_ids:
        return 0
    placeholders = ", ".join(["%s"] * len(policy_ids))
    sql = f"DELETE FROM policy_region WHERE policy_id IN ({placeholders})"
    with conn.cursor() as cur:
        cur.execute(sql, policy_ids)
        deleted = cur.rowcount
    conn.commit()
    return deleted


def run_region_mapping(conn, records: list):
    """이번에 적재한 정책들의 시도/시군구 정보로 policy_region을 다시 계산해 채운다."""
    mapping = load_zipcd_mapping(conn)
    if not mapping:
        return
    plcyno_map = build_plcyno_to_id_map(conn)

    pairs = []
    policy_ids_in_scope = set()
    no_match = 0
    for record in records:
        serv_id = record["servId"]
        detail = record.get("detail") or {}
        summary = record.get("summary") or {}
        ctpv_nm = clean(detail.get("ctpvNm")) or clean(summary.get("ctpvNm"))
        sgg_nm = clean(detail.get("sggNm")) or clean(summary.get("sggNm"))

        plcy_no = PLCYNO_PREFIX + serv_id
        policy_id = plcyno_map.get(plcy_no)
        if policy_id is None:
            continue
        policy_ids_in_scope.add(policy_id)
        if not ctpv_nm:
            continue

        codes = zip_codes_for_region(ctpv_nm, sgg_nm, mapping)
        if not codes:
            no_match += 1
            continue
        pairs.extend((policy_id, code) for code in codes)

    deleted = delete_region_pairs(conn, list(policy_ids_in_scope))
    inserted = insert_region_pairs(conn, pairs)
    print(f"policy_region: 기존 {deleted}건 삭제 후 {inserted}건 재적재 (매칭 안 된 시도명 {no_match}건)")


def main():
    """상세정보 파일 전체를 policy 테이블 형식으로 변환해 upsert하고, 지역 매핑까지 갱신한다."""
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
