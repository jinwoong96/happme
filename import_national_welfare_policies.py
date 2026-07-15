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
    plcyAplyMthdCn = applmetList 중 "신청기관연락처목록" 단계의 안내 텍스트
    srngMthdCn / addAplyQlfcCndCn = slctCritCn (선정기준)
    ptcpPrpTrgtCn / earnEtcCn     = tgtrDtlCn (지원대상 상세 - 지자체 API에 없던 필드라 여기선
                                     sprtTrgtCn 대신 이걸 씀. 소득 조건이 이 텍스트 안에 섞여
                                     있는 경우가 많아 earnEtcCn에도 재사용)
    sprtTrgtMinAge/MaxAge = 19/39 고정값 (WELFARE2.py가 lifeArray=004 청년으로 필터링해서 받음)
    지역(policy_region) = 매핑 안 함. 중앙부처 사업은 시도명(ctpvNm) 자체가 응답에 없고
    전국 단위이므로, 지자체 임포트처럼 지역 매핑을 걸 근거 데이터가 없음.

사전 준비:
    pip install pymysql python-dotenv
    (.env는 기존 스크립트들과 동일한 DB_* 값 사용)
    source 컬럼이 DB에 아직 없다면 먼저 추가(지자체 import 때 이미 추가했다면 생략):
        ALTER TABLE policy ADD COLUMN source VARCHAR(20) NULL AFTER plcySprtCn;

사용법:
    python import_national_welfare_policies.py --peek
        # 1건만 변환해서 어떤 값이 들어가는지 미리보기 (DB 저장 안 함)

    python import_national_welfare_policies.py
        # National_welfare_data_detail.json 전체를 policy 테이블에 적재
"""

import os
import sys
import re
import json
import argparse
from datetime import datetime

import pymysql
from dotenv import load_dotenv

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
    "sprtSclCnt", "sprtTrgtMinAge", "sprtTrgtMaxAge", "earnMinAmt", "earnMaxAmt",
    "earnEtcCn", "earnCndSeCd", "addAplyQlfcCndCn", "ptcpPrpTrgtCn", "mrgSttsCd",
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
    if val is None:
        return None
    val = str(val).strip()
    return val if val else None


def parse_int(val):
    try:
        return int(str(val).strip())
    except (ValueError, TypeError):
        return None


def parse_ymd(val):
    val = clean(val)
    if not val:
        return None
    try:
        return datetime.strptime(val, "%Y%m%d")
    except ValueError:
        return None


def looks_like_url(text: str) -> bool:
    if not text or " " in text:
        return False
    if text.startswith("http://") or text.startswith("https://"):
        return True
    if _PHONE_RE.match(text):
        return False
    return "." in text


def normalize_url(text: str) -> str:
    if text.startswith("http://") or text.startswith("https://"):
        return text
    return "https://" + text


def build_apply_period(detail: dict) -> str:
    cyc = clean(detail.get("sprtCycNm"))
    bgn = clean(detail.get("enfcBgngYmd"))
    end = clean(detail.get("enfcEndYmd"))
    if cyc and "수시" in cyc:
        return "상시(수시)"
    if bgn and end:
        return f"{bgn} ~ {end}"
    return cyc or "상시"


def build_apply_method(detail: dict):
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
    for item in as_list(detail.get("inqplHmpgReldList")):
        if not isinstance(item, dict):
            continue
        link = clean(item.get("servSeDetailLink"))
        if link and looks_like_url(link):
            return normalize_url(link)
    return None


def build_submission_docs(detail: dict) -> str:
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
    return clean(detail.get("intrsThemaArray")) or clean(detail.get("lifeArray")) or "청년"


def build_mclsf(detail: dict) -> str:
    kw = clean(detail.get("intrsThemaArray"))
    if kw:
        return kw.split(",")[0].strip()
    return "기타"


def transform_record(record: dict) -> tuple:
    serv_id = record["servId"]
    summary = record.get("summary") or {}
    detail = record.get("detail") or {}

    tgtr_cn = clean(detail.get("tgtrDtlCn"))
    slct_cn = clean(detail.get("slctCritCn"))

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
        "sprvsnInstCdNm": None,
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
        "sprtTrgtMinAge": 19,
        "sprtTrgtMaxAge": 39,
        "earnMinAmt": None,
        "earnMaxAmt": None,
        "earnEtcCn": tgtr_cn or "-",
        "earnCndSeCd": None,
        "addAplyQlfcCndCn": slct_cn or "-",
        "ptcpPrpTrgtCn": tgtr_cn or "-",
        "mrgSttsCd": None,
        "inqCnt": parse_int(summary.get("inqNum")) or 0,
        "frstRegDt": parse_ymd(summary.get("svcfrstRegTs")),
        "lastMdfcnDt": None,
    }
    return tuple(values[c] for c in COLUMNS)


def load_records() -> list:
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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--peek", action="store_true", help="1건만 변환 결과 미리보기 (DB 저장 안 함)")
    args = parser.parse_args()

    records = load_records()
    print(f"{DETAIL_FILE}에서 상세정보 있는 {len(records)}건 로드")

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
        print("참고: 중앙부처 사업은 지역 정보가 없어 policy_region 매핑은 하지 않았습니다.")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
