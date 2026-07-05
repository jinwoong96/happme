import re

import pandas as pd

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

    def match(self, user: dict, policy: dict) -> dict:
        policy_zip_list = self._parse_zip_list(policy.get("zipCd"))
        policy_region_summary = self._summarize_policy_region(policy_zip_list)

        if not policy_zip_list:
            return make_result(True, "지역 제한 없음", None, policy_region_summary)

        user_region = str(user.get("region", "")).strip()
        user_district = str(user.get("district", "")).strip()

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
        region_prefix = self._region_to_prefix(region)
        if region_prefix is None:
            return None

        candidates = self.zipcd_df[self.zipcd_df["시군구코드"].str.startswith(region_prefix)].copy()

        # 세종특별자치시는 시군구코드가 보통 1개라 district와 무관하게 반환
        if region_prefix == "36" and len(candidates) == 1:
            return candidates.iloc[0]["시군구코드"]

        district = self._normalize_text(district)

        matched = candidates[
            candidates["지역명"].apply(self._normalize_text).str.contains(district, regex=False)
        ]

        if len(matched) == 0:
            return None

        return matched.iloc[0]["시군구코드"]

    @staticmethod
    def _parse_zip_list(zip_cd) -> list[str]:
        if not zip_cd:
            return []
        return [x.strip() for x in str(zip_cd).split(",") if x.strip()]

    def _summarize_policy_region(self, policy_zip_list: list[str], limit: int = 20) -> dict:
        if not policy_zip_list:
            return {"type": "전국", "zipCd_count": 0, "region_names": []}

        if len(policy_zip_list) > limit:
            return {
                "type": "광범위지역",
                "zipCd_count": len(policy_zip_list),
                "region_names": [],
            }

        region_names = []

        for zip_code in policy_zip_list:
            row = self.zipcd_df[self.zipcd_df["시군구코드"] == zip_code]
            if not row.empty:
                sido = row.iloc[0].get("시도명", "")
                sigungu = row.iloc[0].get("시군구명", "")
                region_names.append(f"{sido} {sigungu}".strip())

        return {
            "type": "일부지역",
            "zipCd_count": len(policy_zip_list),
            "region_names": region_names,
        }
