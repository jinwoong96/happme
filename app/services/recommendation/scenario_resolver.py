import pandas as pd

from app.core.settings import settings

REGION_AMBIGUOUS = {
    "경상도": ["경상남도", "경상북도"],
    "전라도": ["전라남도", "전북특별자치도"],
    "충청도": ["충청남도", "충청북도"],
}

SIDO_ABBREVIATIONS = {
    "서울": "서울특별시", "서울시": "서울특별시",
    "부산": "부산광역시", "부산시": "부산광역시",
    "대구": "대구광역시", "대구시": "대구광역시",
    "인천": "인천광역시", "인천시": "인천광역시",
    "광주": "광주광역시", "광주시": "광주광역시",
    "대전": "대전광역시", "대전시": "대전광역시",
    "울산": "울산광역시", "울산시": "울산광역시",
    "세종": "세종특별자치시", "세종시": "세종특별자치시",
    "경기": "경기도", "경기도": "경기도",
    "강원": "강원특별자치도", "강원도": "강원특별자치도",
    "충북": "충청북도", "충청북도": "충청북도",
    "충남": "충청남도", "충청남도": "충청남도",
    "전북": "전북특별자치도", "전라북도": "전북특별자치도",
    "전남": "전라남도", "전라남도": "전라남도",
    "경북": "경상북도", "경상북도": "경상북도",
    "경남": "경상남도", "경상남도": "경상남도",
    "제주": "제주특별자치도", "제주도": "제주특별자치도", "제주특별자치도": "제주특별자치도",
}

EMPLOYMENT_STATUS_VALUES = {
    "재직자", "자영업자", "미취업자", "프리랜서", "일용근로자",
    "(예비)창업자", "단기근로자", "영농종사자", "기타", "제한없음",
}
EMPLOYMENT_STATUS_ALIAS = {
    "취업": "재직자", "재직중": "재직자", "재직 중": "재직자", "회사원": "재직자", "직장인": "재직자", "재직": "재직자",
    "무직": "미취업자", "실직": "미취업자", "퇴사": "미취업자", "퇴직": "미취업자", "무직자": "미취업자", "미취업": "미취업자",
    "취업 준비": "미취업자", "취업준비": "미취업자", "취준생": "미취업자",
    "구직중": "미취업자", "구직 중": "미취업자", "구직자": "미취업자",
    "창업": "(예비)창업자", "사업": "자영업자", "사업자": "자영업자", "자영업자": "자영업자", "자영업": "자영업자",
    "프리랜서": "프리랜서", "프리랜서로 활동": "프리랜서",
    "농사": "영농종사자", "귀농": "영농종사자", "농업": "영농종사자",
    "재학생": "제한없음", "학생": "제한없음", "대학생": "제한없음",
}

# Q2 버튼(이직/퇴사/창업/재직)을 고르면 바로 확정되는 employment_status.
# "이직"과 "재직" 모두 재직자로 귀결되지만, 전자는 상태 변화, 후자는 현재 재직 확인이라는
# 의미 차이가 있어 버튼은 분리하고 로그 문구로 구분한다.
EMPLOYMENT_CHOICE_MAP = {
    "이직": "재직자",
    "퇴사": "미취업자",
    "창업": "(예비)창업자",
    "재직": "재직자",
}


def is_empty(v) -> bool:
    """값이 None이거나 빈 문자열/"None"/"NULL" 같은 사실상 빈 값인지 확인한다."""
    if v is None:
        return True
    if isinstance(v, str) and v.strip() in ("", "None", "NULL"):
        return True
    return False


class ScenarioResolver:
    """
    Q1(지역이동)/Q2(취업 변화) 구조화 답변을 user_profile diff로 변환하는 순수 로직.
    DB 커넥션이나 Watson 호출 없이, bene_ai가 이미 갖고 있는 zipcd_mapping.csv만 사용한다
    (region_matcher.py가 쓰는 것과 동일한 파일).
    """

    def __init__(self, zipcd_csv_path: str | None = None):
        df = pd.read_csv(zipcd_csv_path or settings.zipcd_mapping_path, dtype={"시군구코드": str})
        self._rows = self._parse_rows(df)
        self._sido_names = {row["sido_name"] for row in self._rows}

    @staticmethod
    def _parse_rows(df: pd.DataFrame) -> list[dict]:
        # "지역명" 컬럼은 "경기도 수원시 장안구"처럼 시/도 + 시/군/구가 한 문자열로 붙어 있다.
        rows = []
        for full_name in df["지역명"].astype(str):
            full_name = full_name.strip()
            parts = full_name.split(" ")
            sido_name = parts[0]
            sigungu_name = " ".join(parts[1:]) if len(parts) > 1 else full_name
            rows.append({"sido_name": sido_name, "sigungu_name": sigungu_name, "full_name": full_name})
        return rows

    def _find_district_candidates(self, raw_district: str) -> list[tuple[str, str]]:
        """
        sigungu_name에 raw_district가 부분 문자열로 포함되는 행을 전부 찾는다.
        수원시처럼 하위 구(장안구/권선구/팔달구/영통구)로만 쪼개져 있어 "수원시" 자체가
        정확히 일치하는 행이 없는 경우를 위한 것. 매칭된 행이 같은 시 소속이면 시 단위로
        묶어서 하나의 후보로 처리한다 (구 단위는 추적하지 않는다는 설계 원칙).
        """
        matched = [row for row in self._rows if raw_district in row["sigungu_name"]]
        grouped = {}
        for row in matched:
            parts = row["sigungu_name"].split(" ")
            city_repr = parts[0] if len(parts) > 1 else row["sigungu_name"]
            grouped[(row["sido_name"], city_repr)] = True
        return list(grouped.keys())

    def _normalize_region(self, raw_region: str | None) -> tuple[str | None, bool, str | None]:
        """사용자가 입력한 시/도 이름(줄임말 포함)을 정식 시/도명으로 바꾼다.
        Returns: (정규화된 시/도명 또는 None, 애매한지 여부, 설명 메모)"""
        if is_empty(raw_region):
            return None, False, None
        raw_region = raw_region.strip()

        if raw_region in REGION_AMBIGUOUS:
            return None, True, (
                f"'{raw_region}'는 남/북 등 세부 구분이 안 되는 표현입니다. "
                f"후보: {REGION_AMBIGUOUS[raw_region]} 중 사용자에게 되물어야 합니다."
            )

        if raw_region in self._sido_names:
            return raw_region, False, f"'{raw_region}' 그대로 인정 (zipcd 매핑 확인)"

        mapped = SIDO_ABBREVIATIONS.get(raw_region)
        if mapped and mapped in self._sido_names:
            return mapped, False, f"'{raw_region}' → '{mapped}'로 정규화 (zipcd 매핑 확인)"

        prefix_candidates = [s for s in self._sido_names if s.startswith(raw_region)]
        if len(prefix_candidates) == 1:
            return prefix_candidates[0], False, f"'{raw_region}' → '{prefix_candidates[0]}'로 정규화 (zipcd 접두어 매칭)"

        return None, True, f"'{raw_region}'는 zipcd 매핑에서 유효한 시/도로 확인되지 않습니다."

    def _normalize_district(self, raw_district: str | None) -> tuple[str | None, str | None, bool, str | None]:
        """사용자가 입력한 시/군/구 이름을 zipcd 매핑에 있는 정식 이름으로 바꾼다.
        Returns: (정규화된 시/군/구명, 소속 시/도명, 애매한지 여부, 설명 메모)"""
        if is_empty(raw_district):
            return None, None, False, None
        raw_district = raw_district.strip()

        candidates = self._find_district_candidates(raw_district)

        if not candidates:
            return None, None, True, f"'{raw_district}'는 zipcd 매핑에서 찾을 수 없어 정확한 행정구역을 확정할 수 없습니다."

        if len(candidates) > 1:
            candidates_str = ", ".join(f"{sido} {city}" for sido, city in sorted(candidates))
            return None, None, True, (
                f"'{raw_district}'는 여러 지역({candidates_str})에 해당할 수 있어 자동으로 확정할 수 없습니다."
            )

        sido, city_repr = candidates[0]
        return city_repr, sido, False, f"'{raw_district}' → '{city_repr}'로 정규화 (zipcd 매핑, 소속: {sido})"

    def resolve_region_answer(self, region_choice: str, region_text: str | None) -> tuple[dict, dict, list[str]]:
        """Q1(지역이동) 답변을 user_profile diff로 바꾼다.
        Returns: (반영할 값 diff, 애매해서 반영 보류한 항목, 설명 메모 목록)"""
        notes: list[str] = []
        ambiguous: dict = {}
        diff: dict = {}

        if region_choice in ("지역 이동 안함", "미정"):
            if region_choice == "미정":
                notes.append("사용자가 지역 이동 여부를 모른다고 답해 region/district 변경 없이 진행함")
            return diff, ambiguous, notes

        # region_choice == "지역 쓰기"
        if is_empty(region_text):
            ambiguous["region"] = "지역 쓰기를 선택했지만 입력값이 비어 있어 반영 보류함"
            notes.append(ambiguous["region"])
            return diff, ambiguous, notes

        sigungu_name, derived_sido, district_ambiguous, note = self._normalize_district(region_text)
        if sigungu_name:
            diff["region"] = derived_sido
            diff["district"] = sigungu_name
            notes.append(note)
            return diff, ambiguous, notes
        if district_ambiguous:
            notes.append(note)

        # 시/군/구로 못 찾았으면, 시/도 자체를 입력했을 가능성 시도 (예: "제주도", "강원도")
        normalized_sido, _, note2 = self._normalize_region(region_text)
        if normalized_sido:
            diff["region"] = normalized_sido
            notes.append(note2)
            return diff, ambiguous, notes

        ambiguous["region"] = note2 or note
        notes.append(ambiguous["region"])
        return diff, ambiguous, notes

    @staticmethod
    def _normalize_closed_set(raw_value, allowed_values: set, alias_map: dict, field_label: str) -> tuple[str | None, str | None]:
        """자유 입력값을 정해진 값 집합(allowed_values) 중 하나로 바꾼다. 이미 정확히
        일치하거나 별칭 목록(alias_map)에 있으면 매핑하고, 아니면 반영을 보류한다."""
        if is_empty(raw_value):
            return None, None
        raw_value = str(raw_value).strip()

        if raw_value in allowed_values:
            return raw_value, None

        if raw_value in alias_map:
            mapped = alias_map[raw_value]
            return mapped, f"{field_label}: '{raw_value}' → '{mapped}'로 정규화"

        return None, f"{field_label}: '{raw_value}'는 허용된 값이나 별칭 목록에 없어 반영 보류함"

    def resolve_employment_answer(self, employment_choice: str, other_text: str | None) -> tuple[dict, dict, list[str]]:
        """Q2(취업 변화) 답변을 user_profile diff로 바꾼다.
        Returns: (반영할 값 diff, 애매해서 반영 보류한 항목, 설명 메모 목록)"""
        notes: list[str] = []
        ambiguous: dict = {}
        diff: dict = {}

        if employment_choice == "없음":
            notes.append("사용자가 회사 관련 변화가 없다고 답해 employment_status 변경 없이 진행함")
            return diff, ambiguous, notes

        if employment_choice in EMPLOYMENT_CHOICE_MAP:
            value = EMPLOYMENT_CHOICE_MAP[employment_choice]
            diff["employment_status"] = value
            notes.append(f"사용자 선택 '{employment_choice}' → employment_status='{value}'로 반영")
            return diff, ambiguous, notes

        # employment_choice == "기타"
        if is_empty(other_text):
            ambiguous["employment_status"] = "기타를 선택했지만 입력값이 비어 있어 반영 보류함"
            notes.append(ambiguous["employment_status"])
            return diff, ambiguous, notes

        validated, note = self._normalize_closed_set(
            other_text, EMPLOYMENT_STATUS_VALUES, EMPLOYMENT_STATUS_ALIAS, "employment_status"
        )
        if validated:
            diff["employment_status"] = validated
            notes.append(note or f"기타 입력 '{other_text}' → '{validated}'로 반영")
            return diff, ambiguous, notes

        ambiguous["employment_status"] = note
        notes.append(note)
        return diff, ambiguous, notes

    def resolve(
        self,
        region_choice: str,
        region_text: str | None,
        employment_choice: str,
        employment_other: str | None,
    ) -> tuple[dict, dict, list[str]]:
        """Q1(지역이동)+Q2(취업 변화) 답변을 합쳐 최종 user_profile diff를 만든다.
        지역만 바뀌고 시/군/구가 확정되지 않으면 기존 district 값을 지운다(남아있으면
        예전 지역의 구가 새 시/도에 잘못 붙어있는 상태가 되므로)."""
        diff: dict = {}
        ambiguous: dict = {}
        notes: list[str] = []

        r_diff, r_ambiguous, r_notes = self.resolve_region_answer(region_choice, region_text)
        diff.update(r_diff)
        ambiguous.update(r_ambiguous)
        notes.extend(r_notes)

        e_diff, e_ambiguous, e_notes = self.resolve_employment_answer(employment_choice, employment_other)
        diff.update(e_diff)
        ambiguous.update(e_ambiguous)
        notes.extend(e_notes)

        # region은 확정됐는데 district가 이번에 확정되지 않았다면(시/도만 입력한 경우),
        # 이전 지역의 district가 그대로 남아있으면 안 되므로 null로 초기화한다.
        if "region" in diff and "district" not in diff:
            diff["district"] = None
            notes.append(
                "지역(region)이 변경됐지만 시/군/구(district)가 이번에 확정되지 않아 기존 값이 아닌 null로 초기화함"
            )

        return diff, ambiguous, notes
