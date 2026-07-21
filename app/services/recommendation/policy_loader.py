import pymysql

from app.core.settings import settings

# eligibility_rules.py/region_matcher.py/recommendation_service.py 등 추천 흐름 전체가
# policy dict에서 읽는 필드 전부.
FIELDS = [
    "policy_id", "plcyNo", "plcyNm", "plcyExplnCn", "plcySprtCn", "plcyKywdNm",
    "lclsfNm", "mclsfNm", "rgtrInstCdNm",
    "aplyPrdSeCd", "aplyYmd", "sprtTrgtAgeLmtYn", "sprtTrgtMinAge", "sprtTrgtMaxAge",
    "mrgSttsCd", "schoolCd", "plcyMajorCd", "sbizCd", "jobCd",
    "earnCndSeCd", "earnEtcCn", "earnMinAmt", "earnMaxAmt",
]

# region_matcher.py가 policy.get("zipCd")로 쉼표구분 문자열을 기대하므로,
# policy_region 테이블을 GROUP_CONCAT으로 묶어서 재구성한다.
ZIP_QUERY = """
    SELECT policy_id, GROUP_CONCAT(zip_code ORDER BY zip_code) AS zipCd
    FROM policy_region
    GROUP BY policy_id
"""


class PolicyLoaderService:
    """
    정책 전체 데이터를 로드/보관합니다. SearchService와 동일하게 RDS MySQL의 policy
    테이블에서 직접 조회합니다(정적 JSON 스냅샷을 쓰지 않음 - 서버 재시작 시점 기준으로
    항상 최신 DB 상태를 반영).
    무거운 리소스이므로 앱 시작 시(lifespan) 인스턴스 하나만 만들어 재사용하세요.
    """

    def __init__(self):
        print("[PolicyLoaderService] RDS에서 정책 데이터 로드 중...")
        self.policies: list[dict] = self._load_policies_from_db()
        print(f"[PolicyLoaderService] 총 {len(self.policies)}개 정책 로드")

        self._by_plcyno: dict[str, dict] = {
            str(p.get("plcyNo")): p for p in self.policies if p.get("plcyNo") is not None
        }

    @staticmethod
    def _load_policies_from_db() -> list[dict]:
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

        return policies

    def get_policies(self) -> list[dict]:
        return self.policies

    def get_policy_by_plcyno(self, plcy_no: str) -> dict | None:
        return self._by_plcyno.get(str(plcy_no))
