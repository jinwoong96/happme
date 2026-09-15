import re

import pandas as pd

from app.core.match_timing_debug import timed  # TODO(임시/테스트 전용): 측정 끝나면 이 줄과 @timed(...) 제거
from app.core.settings import settings
from app.services.recommendation.rule_helpers import make_result

# 시도명 정규화용
REGION_ALIASES = {
    "서울": "서울특별시",
    "서울시": "서울특별시",
    "부산": "부산광역시",
    "부산시": "부산광역시",
    "대구": "대구광역시",
    "인천": "인천광역시",
    "광주": "광주광역시",
    "대전": "대전광역시",
    "울산": "울산광역시",
    "세종": "세종특별자치시",
    "경기": "경기도",
    "강원": "강원특별자치도",
    "충북": "충청북도",
    "충남": "충청남도",
    "전북": "전북특별자치도",
    "전남": "전라남도",
    "경북": "경상북도",
    "경남": "경상남도",
    "제주": "제주특별자치도",
}

# 시도명 -> 법정동코드 앞 2자리
PREFIX_MAP = {
    "서울특별시": "11",
    "부산광역시": "26",
    "대구광역시": "27",
    "인천광역시": "28",
    "광주광역시": "29",
    "대전광역시": "30",
    "울산광역시": "31",
    "세종특별자치시": "36",
    "경기도": "41",
    "강원특별자치도": "51",
    "충청북도": "43",
    "충청남도": "44",
    "전북특별자치도": "52",
    "전라남도": "46",
    "경상북도": "47",
    "경상남도": "48",
    "제주특별자치도": "50",
}


class RegionMatcher:
    """
    시군구코드 매핑(zipcd_mapping.csv)을 이용해 사용자 지역과 정책 지역 조건을 대조합니다.
    무거운 리소스(csv)이므로 앱 시작 시(lifespan) 인스턴스 하나만 만들어 재사용하세요.
    """

    def __init__(self):
        self.zipcd_df = pd.read_csv(settings.zipcd_mapping_path, dtype={"시군구코드": str})

        # match()가 호출될 때마다(정책 x persona 조합으로 수만 번) 아래 값들을 pandas로 매번
        # 다시 계산하고 있어서(전체 스캔이 호출당 20~40번) 그게 region 체크 시간의 대부분을
        # 차지했다(프로파일링 결과 region 체크가 캐시미스 전체 시간의 96.7%). 정책/사용자가
        # 바뀌어도 안 바뀌는 값들이라 __init__에서 한 번만 계산해 캐싱한다.
        self._all_known_zips: set[str] = set(self.zipcd_df["시군구코드"])

        # 시/도 prefix -> [(시군구코드, 정규화된 지역명), ...] (원본 DataFrame 행 순서 유지 -
        # _get_zip_code의 "첫 매칭" 동작이 이 순서에 의존한다)
        self._province_rows: dict[str, list[tuple[str, str]]] = {}
        for prefix in PREFIX_MAP.values():
            sub = self.zipcd_df[self.zipcd_df["시군구코드"].str.startswith(prefix)]
            self._province_rows[prefix] = [
                (zip_code, self._normalize_text(name))
                for zip_code, name in zip(sub["시군구코드"], sub["지역명"])
            ]

        # 시/도 prefix -> 그 시/도에 속한 시군구코드 전체 집합 (전국/시도범위 판정용)
        self._province_zip_sets: dict[str, set[str]] = {
            prefix: {zip_code for zip_code, _ in rows} for prefix, rows in self._province_rows.items()
        }

        # 시군구코드 -> 지역명 (region_names 조립용)
        self._zip_to_name: dict[str, str] = dict(
            zip(self.zipcd_df["시군구코드"], self.zipcd_df["지역명"].astype(str).str.strip())
        )

    @timed("region")
    def match(self, user: dict, policy: dict) -> dict:
        """사용자 거주지역이 정책의 지역 조건(zipCd 목록)에 포함되는지 확인한다.
        사용자가 시/군/구까지 안 정했으면 시/도 단위로만 대략 맞춰본다."""
        policy_zip_list = self._parse_zip_list(policy.get("zipCd"))
        policy_region_summary = self._summarize_policy_region(policy_zip_list)

        if not policy_zip_list:
            return make_result(True, "지역 제한 없음", None, policy_region_summary)

        # user.get(...)이 None을 반환할 수 있는데(키는 있지만 값이 None), str(None)은 빈 문자열이
        # 아니라 "None"이라는 문자열이 되어버려 아래 empty-check를 무력화한다. or ""로 먼저 걸러낸다.
        user_region = str(user.get("region") or "").strip()
        user_district = str(user.get("district") or "").strip()

        # 시/군/구를 특정하지 않은 경우(시/도만 입력) _get_zip_code는 그 시/도의 첫 번째 구를
        # 임의로 골라버려서 실제로는 다른 구 대상 정책까지 전부 "지역 불충족"으로 오판하게 된다.
        # 시/도만 아는 상태이므로, 정책의 zipCd 목록에 그 시/도 소속 구가 하나라도 있으면 충족으로 본다.
        if not user_district:
            region_prefix = self._region_to_prefix(user_region)
            if region_prefix is None:
                return make_result(
                    False, "사용자 지역코드 변환 실패", {"region_name": user_region}, policy_region_summary
                )

            if any(zip_code.startswith(region_prefix) for zip_code in policy_zip_list):
                return make_result(
                    True, "지역(시/도) 조건 충족", {"region_name": user_region}, policy_region_summary
                )

            return make_result(
                False, "지역 조건 불충족", {"region_name": user_region}, policy_region_summary
            )

        user_zip = self._get_zip_code(user_region, user_district)

        if not user_zip:
            return make_result(
                False,
                "사용자 지역코드 변환 실패",
                {"region_name": f"{user_region} {user_district}"},
                policy_region_summary,
            )

        if user_zip not in policy_zip_list:
            return make_result(
                False,
                "지역 조건 불충족",
                {
                    "zipCd": user_zip,
                    "region_name": f"{user_region} {user_district}",
                },
                policy_region_summary,
            )

        return make_result(
            True,
            "지역 조건 충족",
            {
                "zipCd": user_zip,
                "region_name": f"{user_region} {user_district}",
            },
            policy_region_summary,
        )

    @staticmethod
    def _normalize_text(text) -> str:
        """공백 제거 + 기본 문자열 정리"""
        if text is None:
            return ""
        return re.sub(r"\s+", "", str(text).strip())

    @classmethod
    def _normalize_region(cls, region: str) -> str:
        """서울, 전남 같은 축약명을 정식 시도명으로 변환"""
        region = cls._normalize_text(region)

        if region in REGION_ALIASES:
            return REGION_ALIASES[region]

        for short, full in REGION_ALIASES.items():
            if short in region or region in full:
                return full

        return region

    @classmethod
    def _region_to_prefix(cls, region: str) -> str | None:
        return PREFIX_MAP.get(cls._normalize_region(region))

    def _get_zip_code(self, region: str, district: str) -> str | None:
        """시/도 + 시/군/구 이름으로 시군구코드를 찾는다. 못 찾으면 None."""
        region_prefix = self._region_to_prefix(region)
        if region_prefix is None:
            return None

        candidates = self._province_rows.get(region_prefix, [])

        # 세종특별자치시는 시군구코드가 보통 1개라 district와 무관하게 반환
        if region_prefix == "36" and len(candidates) == 1:
            return candidates[0][0]

        district = self._normalize_text(district)

        for zip_code, normalized_name in candidates:
            if district in normalized_name:
                return zip_code

        return None

    @staticmethod
    def _parse_zip_list(zip_cd) -> list[str]:
        """쉼표로 구분된 시군구코드 문자열을 리스트로 쪼갠다."""
        if not zip_cd:
            return []
        return [x.strip() for x in str(zip_cd).split(",") if x.strip()]

    # 정책의 zipCd가 전체 시군구코드의 이 비율 이상을 포함하면(예: 지역 몇 곳 데이터 누락 등으로
    # 100%가 아니어도) 사실상 전국 단위 정책으로 취급한다.
    _NATIONWIDE_COVERAGE_RATIO = 0.95

    def _summarize_policy_region(self, policy_zip_list: list[str], limit: int = 20) -> dict:
        """
        정책의 지역 범위를 화면 탭 분류용으로 3단계로 나눈다.
        - 광역: 지역 제한이 없거나(zipCd 없음), 전체 시군구코드를 사실상 다 포함하거나,
          시/도 전역을 2개 이상 포함(여러 시/도에 걸침) - 전국 단위와 여러 시/도 단위를 하나로 묶음
        - 시도범위: 특정 시/도 산하 시군구코드를 전부 포함(그 시/도 하나 전역 대상)
        - 시군구범위: 그 외 - 특정 시/군/구 단위로만 한정
        """
        if not policy_zip_list:
            return {"type": "광역", "zipCd_count": 0, "region_names": []}

        zip_set = set(policy_zip_list)
        all_known = self._all_known_zips

        if all_known and len(zip_set & all_known) / len(all_known) >= self._NATIONWIDE_COVERAGE_RATIO:
            return {"type": "광역", "zipCd_count": len(policy_zip_list), "region_names": []}

        full_province_count = sum(
            1
            for province_codes in self._province_zip_sets.values()
            if province_codes and province_codes.issubset(zip_set)
        )

        if full_province_count >= 2:
            return {"type": "광역", "zipCd_count": len(policy_zip_list), "region_names": []}
        if full_province_count == 1:
            return {"type": "시도범위", "zipCd_count": len(policy_zip_list), "region_names": []}

        if len(policy_zip_list) > limit:
            return {"type": "시군구범위", "zipCd_count": len(policy_zip_list), "region_names": []}

        region_names = [
            self._zip_to_name[zip_code] for zip_code in policy_zip_list if zip_code in self._zip_to_name
        ]

        return {
            "type": "시군구범위",
            "zipCd_count": len(policy_zip_list),
            "region_names": region_names,
        }
