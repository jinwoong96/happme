"""
복지로(지자체/중앙부처) 정책 임포트 스크립트 공용 모듈 - 지원 연령(sprtTrgtMinAge/MaxAge)과
연령제한없음 플래그(sprtTrgtAgeLmtYn)를 결정한다.

import_welfare_policies.py(지자체)/import_national_welfare_policies.py(중앙부처)가 이 모듈의
resolve_age()를 공통으로 호출한다. 두 소스는 생애주기 필드명만 다르고("lifeNmArray" vs
"lifeArray") 값 형식(콤마로 구분된 생애주기 이름 목록)은 동일해서, 이 모듈은 그 값 자체(문자열)만
받는다.

우선순위: 본문 텍스트(sprtTrgtCn/tgtrDtlCn)에서 뽑은 값 > 생애주기(lifeNmArray/lifeArray) 기반 값.
텍스트 신호가 애매하거나(같은 쪽에서 서로 다른 값이 여러 개 나옴) 생애주기 기반값과 충돌하면
(min > max가 됨) 텍스트를 신뢰하지 않고 생애주기 기반값으로 되돌린다 - 텍스트 파싱은 정규식 기반이라
완전할 수 없고, 애매한 걸 억지로 봉합하는 것보다는 생애주기 쪽이 더 안전하다는 판단.
"""

import re

# 생애주기 -> (시작나이, 끝나이). 순서 자체가 생애주기 순서라 비연속 구간(클러스터) 판정에 쓰인다.
# 청년(19-34)은 청년기본법 제3조 기준, 노년(65-99)은 노인복지법 65세 기준(상한은 실질 무제한이라
# DB 컬럼상 정수 상한이 필요할 때 관행적으로 쓰는 99를 채택). 나머지는 그 사이를 겹침/공백 없이 채움.
LIFE_STAGE_BOUNDS = {
    "영유아": (0, 6),
    "아동": (7, 12),
    "청소년": (13, 18),
    "청년": (19, 34),
    "중장년": (35, 64),
    "노년": (65, 99),
}
LIFE_ORDER = list(LIFE_STAGE_BOUNDS.keys())
PREGNANCY_LABEL = "임신 · 출산"

# 이 서비스 자체가 청년정책 서비스라, 비연속 생애주기 구간에서는 청년이 속한 클러스터만 채택한다.
ANCHOR = "청년"


def _parse_life_categories(life_value: str | None) -> list[str]:
    if not life_value:
        return []
    return [c.strip() for c in life_value.split(",") if c.strip() and c.strip() != PREGNANCY_LABEL]


def _life_base(life_value: str | None) -> tuple[int, int, str | None]:
    """lifeNmArray/lifeArray 값으로 (min, max, age_lmt_yn) base를 계산한다.
    임신·출산을 뺀 6개 생애주기가 전부 있으면 사실상 전연령 대상이므로 age_lmt_yn='Y'를 반환한다
    (min/max 컬럼은 NOT NULL이라 0/99를 채워두지만, eligibility_rules.py의 _match_age는
    sprtTrgtAgeLmtYn='Y'면 이 값들을 아예 보지 않는다)."""
    categories = _parse_life_categories(life_value)
    known = [c for c in categories if c in LIFE_STAGE_BOUNDS]

    if known and set(known) == set(LIFE_ORDER):
        return 0, 99, "Y"

    if ANCHOR not in known:
        # WELFARE.py/WELFARE2.py가 lifeArray=004(청년)로 필터링해서 받아온 데이터라 실제로는
        # 항상 청년이 포함되지만, 방어적으로 청년 단독 범위를 기본값으로 둔다.
        lo, hi = LIFE_STAGE_BOUNDS[ANCHOR]
        return lo, hi, None

    idx_set = {LIFE_ORDER.index(c) for c in known}
    anchor_idx = LIFE_ORDER.index(ANCHOR)

    # anchor_idx를 포함하는 연속 구간(클러스터)의 시작/끝 인덱스를 찾는다.
    start = end = anchor_idx
    while (start - 1) in idx_set:
        start -= 1
    while (end + 1) in idx_set:
        end += 1

    min_age = LIFE_STAGE_BOUNDS[LIFE_ORDER[start]][0]
    max_age = LIFE_STAGE_BOUNDS[LIFE_ORDER[end]][1]
    return min_age, max_age, None


# --- 본문 텍스트 나이 추출 ---
# "세대"(가구 단위)를 나이로 오인하지 않도록, 뒤에 다른 숫자/이상/이하/미만/초과가 안 붙는 단순
# "OO~OO세" 패턴에만 (?!대) 가드를 둔다(그 외 패턴은 "세" 뒤에 이상/이하/미만/초과가 필수라
# "세대"와 애초에 안 겹친다).
_PAIR_TILDE = re.compile(
    r"(?:만\s*)?(\d{1,3})\s*세?\s*[~\-]\s*(?:만\s*)?(\d{1,3})\s*세(?!대)\s*(이하|미만)?"
)
_PAIR_BOTH = re.compile(
    r"(?:만\s*)?(\d{1,3})\s*세\s*(이상|초과)\s*[~\-]?\s*(?:만\s*)?(\d{1,3})\s*세\s*(이하|미만)"
)
_SINGLE_LOWER = re.compile(r"(?:만\s*)?(\d{1,3})\s*세\s*(이상|초과)")
_SINGLE_UPPER = re.compile(r"(?:만\s*)?(\d{1,3})\s*세\s*(이하|미만)")


def _extract_from_text(text: str) -> tuple[int | None, int | None]:
    pair_mins: list[int] = []
    pair_maxs: list[int] = []
    pair_spans: list[tuple[int, int]] = []

    for m in _PAIR_TILDE.finditer(text):
        lo, hi = int(m.group(1)), int(m.group(2))
        if m.group(3) == "미만":
            hi -= 1
        pair_mins.append(lo)
        pair_maxs.append(hi)
        pair_spans.append(m.span())

    for m in _PAIR_BOTH.finditer(text):
        lo, hi = int(m.group(1)), int(m.group(3))
        if m.group(2) == "초과":
            lo += 1
        if m.group(4) == "미만":
            hi -= 1
        pair_mins.append(lo)
        pair_maxs.append(hi)
        pair_spans.append(m.span())

    if pair_mins:
        # 여러 그룹(예: "12~17세 남성청소년, 18~26세 여성")이 섞여 있어도 전체 min~max로 병합한다.
        return min(pair_mins), max(pair_maxs)

    def _not_in_pair_span(span: tuple[int, int]) -> bool:
        return not any(s[0] <= span[0] < s[1] for s in pair_spans)

    lower_values = {
        int(m.group(1)) + (1 if m.group(2) == "초과" else 0)
        for m in _SINGLE_LOWER.finditer(text)
        if _not_in_pair_span(m.span())
    }
    upper_values = {
        int(m.group(1)) - (1 if m.group(2) == "미만" else 0)
        for m in _SINGLE_UPPER.finditer(text)
        if _not_in_pair_span(m.span())
    }

    # 같은 쪽에서 서로 다른 값이 2개 이상 나오면 서로 다른 조건으로 갈라지는 문장일 수 있어
    # (예: 대상군별로 다른 상한이 각각 언급됨) 신뢰하지 않고 None으로 둬 생애주기 기반값을 쓴다.
    text_min = next(iter(lower_values)) if len(lower_values) == 1 else None
    text_max = next(iter(upper_values)) if len(upper_values) == 1 else None

    return text_min, text_max


def resolve_age(life_value: str | None, text: str | None) -> tuple[int, int, str | None]:
    """(sprtTrgtMinAge, sprtTrgtMaxAge, sprtTrgtAgeLmtYn)을 반환한다."""
    base_min, base_max, lmt_yn = _life_base(life_value)
    if lmt_yn == "Y":
        return base_min, base_max, "Y"

    text_min, text_max = _extract_from_text(text or "")

    final_min = text_min if text_min is not None else base_min
    final_max = text_max if text_max is not None else base_max

    if final_min > final_max:
        # 텍스트 신호가 생애주기 기반값과 충돌하면(예: 비연속 구간이라 base=19~34인데 텍스트는
        # "65세 이상") 텍스트를 버리고 생애주기 기반값으로 되돌린다.
        final_min, final_max = base_min, base_max

    return final_min, final_max, None
