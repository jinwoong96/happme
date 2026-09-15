# DB 기준으로 data/policy_list.json을 임시로 만드는 스크립트
#
# 원칙은 "온통청년 등 원본 API로 JSON을 먼저 만들고 그걸로 DB를 채운다"이지만, 그 JSON을
# 아직 완전히 갖추기 전까지 검색문서/카드 요약/추천 엔진 파이프라인을 당장 테스트/사용하기
# 위한 임시 조치다. 최종적으로는 이 스크립트와 이 파일 모두 없어질 예정.
#
# aplyPrdSeCd/sprtTrgtAgeLmtYn/schoolCd/plcyMajorCd/sbizCd/jobCd(온통청년 자격조건
# 코드)는 이제 DB 컬럼으로 존재하지만, ONTONG 원본에서 백필된 정책만 채워져 있고
# BOKJIRO/MANUAL 등 다른 소스는 계속 NULL이다(그 소스엔 애초에 이 코드 체계가 없음).
#
# 실행 위치: ai/
# 사용법: python -m code_create_policy_search_docs.build_policy_list_from_db_temp

import json
from datetime import date, datetime
from pathlib import Path

import pymysql

from app.core.settings import settings

OUTPUT_FILE = "data/policy_list.json"

FIELDS = [
    "policy_id", "plcyNo", "plcyNm", "plcyKywdNm", "plcyExplnCn", "lclsfNm", "mclsfNm",
    "plcySprtCn", "source", "rgtrInstCdNm", "maxSprtAmt", "summary",
    "sprvsnInstCdNm", "sprvsnInstPicNm", "operInstCdNm", "operInstPicNm",
    "bizPrdBgngYmd", "bizPrdEndYmd", "bizPrdEtcCn", "plcyAplyMthdCn", "srngMthdCn",
    "aplyUrlAddr", "sbmsnDcmntCn", "aplyYmd", "aplyEndDt", "refUrlAddr1", "refUrlAddr2",
    "etcMttrCn", "sprtSclCnt", "sprtTrgtMinAge", "sprtTrgtMaxAge", "sprtTrgtAgeLmtYn",
    "earnMinAmt", "earnMaxAmt", "earnEtcCn", "earnCndSeCd",
    "aplyPrdSeCd", "schoolCd", "plcyMajorCd", "sbizCd", "jobCd",
    "addAplyQlfcCndCn", "ptcpPrpTrgtCn", "mrgSttsCd",
    "inqCnt", "bookmarkCnt", "createdAt", "updatedAt",
]

# 라이브 앱의 region_matcher.py가 policy.get("zipCd")로 쉼표구분 문자열을 기대하므로,
# policy_region 테이블을 GROUP_CONCAT으로 묶어서 재구성한다.
ZIP_QUERY = """
    SELECT policy_id, GROUP_CONCAT(zip_code ORDER BY zip_code) AS zipCd
    FROM policy_region
    GROUP BY policy_id
"""


def _json_default(value):
    """json.dump가 date/datetime처럼 기본적으로 직렬화 못 하는 값을 문자열로 바꿔준다."""
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    raise TypeError(f"직렬화할 수 없는 값: {value!r}")


def main():
    """DB의 정책 전체와 지역코드(zipCd)를 읽어 data/policy_list.json으로 저장한다."""
    conn = pymysql.connect(
        host=settings.db_host, port=settings.db_port, user=settings.db_user,
        password=settings.db_password, db=settings.db_name, charset="utf8mb4",
        cursorclass=pymysql.cursors.DictCursor,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"SELECT {', '.join(FIELDS)} FROM policy")
            policies = cursor.fetchall()

            # GROUP_CONCAT은 세션 기본값(1024자)을 넘으면 조용히 잘라버린다. 지역코드가
            # 많은(200개 이상) 전국/광역 단위 정책의 zipCd가 중간에 끊겨 나오는 문제가 있어
            # 세션 한도를 넉넉히 올려준다.
            cursor.execute("SET SESSION group_concat_max_len = 1000000")
            cursor.execute(ZIP_QUERY)
            zip_by_policy_id = {row["policy_id"]: row["zipCd"] for row in cursor.fetchall()}
    finally:
        conn.close()

    for p in policies:
        p["zipCd"] = zip_by_policy_id.get(p["policy_id"])

    print(f"DB에서 읽은 정책 수: {len(policies)}")

    # PolicyLoaderService(라이브 앱)는 언랩 로직 없이 json.load() 결과를 곧바로 리스트로
    # 취급하므로, {"result": {"youthPolicyList": [...]}}로 감싸지 않고 순수 리스트로 저장한다.
    path = Path(OUTPUT_FILE)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(policies, f, ensure_ascii=False, indent=2, default=_json_default)

    print(f"저장 완료: {OUTPUT_FILE}")
    print(
        "참고: aplyPrdSeCd/sprtTrgtAgeLmtYn/schoolCd/plcyMajorCd/sbizCd/jobCd는 "
        "ONTONG 원본에서 백필된 정책만 값이 있고, 나머지 소스(BOKJIRO/MANUAL 등)는 NULL입니다."
    )


if __name__ == "__main__":
    main()
