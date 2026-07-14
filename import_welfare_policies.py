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
    rgtrInstCdNm   = bizChrDeptNm
    plcyAplyMthdCn = aplyMtdCn (없으면 aplyMtdNm)
    srngMthdCn / addAplyQlfcCndCn = slctCritCn (선정기준)
    ptcpPrpTrgtCn / earnEtcCn     = sprtTrgtCn (복지로엔 소득조건이 따로 없어 지원대상 원문 재사용)
    sprtTrgtMinAge/MaxAge = 19/39 고정값 (복지로 API 자체를 lifeArray=004 청년으로만 조회했으므로)
    지역(ctpvNm, 시도명) -> policy_region.zip_code는 bene_ai/data/zipcd_mapping.csv로 접두 매칭
    (예: ctpvNm="대전광역시" -> 지역명이 "대전광역시"로 시작하는 시군구코드 전부 매핑)

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
import csv
import json
import argparse
from datetime import datetime
from pathlib import Path

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

DETAIL_FILE = "welfare_data_detail.json"
ZIPCD_CSV = Path(__file__).resolve().parent.parent / "bene_ai" / "data" / "zipcd_mapping.csv"
PLCYNO_PREFIX = "BOKJIRO-"

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


def build_apply_period(detail: dict) -> str:
    cyc = clean(detail.get("sprtCycNm"))
    bgn = clean(detail.get("enfcBgngYmd"))
    end = clean(detail.get("enfcEndYmd"))
    if cyc and "수시" in cyc:
        return "상시(수시)"
    if bgn and end:
        return f"{bgn} ~ {end}"
    return cyc or "상시"


def build_submission_docs(detail: dict) -> str:
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
    for item in as_list(detail.get("inqplHmpgReldList")):
        if not isinstance(item, dict):
            continue
        url = clean(item.get("wlfareInfoReldCn"))
        if url and url.startswith("http"):
            return url
    return None


def build_keyword(detail: dict) -> str:
    return clean(detail.get("intrsThemaNmArray")) or clean(detail.get("lifeNmArray")) or "청년"


def build_mclsf(detail: dict) -> str:
    kw = clean(detail.get("intrsThemaNmArray"))
    if kw:
        return kw.split(",")[0].strip()
    return "기타"


def transform_record(record: dict) -> tuple:
    serv_id = record["servId"]
    summary = record.get("summary") or {}
    detail = record.get("detail") or {}

    trgt_cn = clean(detail.get("sprtTrgtCn"))
    slct_cn = clean(detail.get("slctCritCn"))
    apply_url = build_apply_url(detail)

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
        "sprvsnInstCdNm": None,
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
        "sprtTrgtMinAge": 19,
        "sprtTrgtMaxAge": 39,
        "earnMinAmt": None,
        "earnMaxAmt": None,
        "earnEtcCn": trgt_cn or "-",
        "earnCndSeCd": None,
        "addAplyQlfcCndCn": slct_cn or "-",
        "ptcpPrpTrgtCn": trgt_cn or "-",
        "mrgSttsCd": None,
        "inqCnt": parse_int(detail.get("inqNum")) or 0,
        "frstRegDt": None,
        "lastMdfcnDt": parse_ymd(detail.get("lastModYmd")),
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


def load_zipcd_mapping() -> list:
    """[(시군구코드, 지역명), ...]"""
    if not ZIPCD_CSV.exists():
        print(f"[경고] {ZIPCD_CSV} 를 찾지 못해 지역 매핑을 건너뜁니다.")
        return []
    rows = []
    with open(ZIPCD_CSV, encoding="utf-8-sig") as f:  # 파일에 UTF-8 BOM이 있어 utf-8-sig로 읽어야 함
        reader = csv.DictReader(f)
        for row in reader:
            code = (row.get("시군구코드") or "").strip()
            name = (row.get("지역명") or "").strip()
            if code and name:
                rows.append((code, name))
    return rows


def zip_codes_for_ctpv(ctpv_nm: str, mapping: list) -> list:
    ctpv_nm = (ctpv_nm or "").strip()
    if not ctpv_nm:
        return []
    return [code for code, name in mapping if name.startswith(ctpv_nm)]


def build_plcyno_to_id_map(conn) -> dict:
    with conn.cursor() as cur:
        cur.execute("SELECT policy_id, plcyNo FROM policy WHERE plcyNo LIKE %s", (f"{PLCYNO_PREFIX}%",))
        rows = cur.fetchall()
    return {plcy_no: policy_id for policy_id, plcy_no in rows}


def insert_region_pairs(conn, pairs: list, batch_size: int = 1000) -> int:
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
    mapping = load_zipcd_mapping()
    if not mapping:
        return
    plcyno_map = build_plcyno_to_id_map(conn)

    pairs = []
    no_match = 0
    for record in records:
        serv_id = record["servId"]
        detail = record.get("detail") or {}
        summary = record.get("summary") or {}
        ctpv_nm = clean(detail.get("ctpvNm")) or clean(summary.get("ctpvNm"))

        plcy_no = PLCYNO_PREFIX + serv_id
        policy_id = plcyno_map.get(plcy_no)
        if policy_id is None or not ctpv_nm:
            continue

        codes = zip_codes_for_ctpv(ctpv_nm, mapping)
        if not codes:
            no_match += 1
            continue
        pairs.extend((policy_id, code) for code in codes)

    inserted = insert_region_pairs(conn, pairs)
    print(f"policy_region: {inserted}건 적재 시도 (매칭 안 된 시도명 {no_match}건)")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--peek", action="store_true", help="1건만 변환 결과 미리보기 (DB 저장 안 함)")
    parser.add_argument("--skip-region", action="store_true", help="policy_region 매핑 생략")
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

        if not args.skip_region:
            run_region_mapping(conn, records)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
