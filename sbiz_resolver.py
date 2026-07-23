"""
복지로(지자체/중앙부처) 정책 임포트 스크립트 공용 모듈 - 특수계층 코드(sbizCd)를 결정한다.

sbizCd는 ONTONG 원본의 고정 코드 체계(SBIZ_MAP, ai/app/services/recommendation/code_mapping.py)라
없는 코드를 새로 만들어 넣으면 eligibility_rules.py의 _match_sbiz()가 "매핑 안 된 코드 = 제한없음"으로
해석해 오히려 필터링이 풀려버린다(정책이 실제로는 특정 계층 전용인데 전체 공개로 보임). 그래서 이미
코드+체커+user_profile 필드가 갖춰진 카테고리만 다룬다:

    장애인        -> "0014005" (user.disability)
    여성(임신출산) -> "0014002" (user.gender == "여")
    한부모·조손    -> "0014004" (user.single_parent, "조손"까지 느슨하게 포함해서 재사용)

보훈대상자/저소득/다문화·탈북민/다자녀는 trgterIndvdlNmArray/trgterIndvdlArray 원본에는 나오지만
대응하는 코드/체커/user_profile 필드가 아직 없어 이 모듈에서는 다루지 않는다.

우선순위: trgterIndvdlNmArray(지자체)/trgterIndvdlArray(중앙부처) 구조화 필드 > 본문 텍스트.
구조화 필드가 하나라도 채워져 있으면 그 자체를 복지로가 이미 완결적으로 분류한 것으로 보고 그대로
믿는다(예: "저소득"만 찍혀 있으면 장애인/한부모 텍스트 언급이 있어도 무시). 필드가 아예 비어있는
레코드에 한해서만 "제목과 타겟텍스트(sprtTrgtCn/tgtrDtlCn + slctCritCn)에 키워드가 동시에 나오는
경우"로 보수적으로 판단한다 - 제목에만 나오거나 텍스트에만 나오는 건 다른 취약계층을 나열한 범용
복지정책에서 우연히 언급된 경우가 대부분이라 채택하지 않는다(실측 검증: 장애인/보훈/한부모 전부
"제목+텍스트 동시" 사례는 5/5, 2/2 전부 정확했고 "텍스트 단독"은 대부분 오탐이었음).
"""

DISABILITY_CODE = "0014005"
WOMAN_CODE = "0014002"
SINGLE_PARENT_CODE = "0014004"

DISABILITY_KEYWORDS = ("장애인",)
# trgterIndvdlNmArray 원본 카테고리명은 "한부모·조손"으로 묶여 있어 구조화 필드 쪽은 그대로 두지만,
# 텍스트 폴백(구조화 필드가 비어있을 때만 쓰는 보수적 판단)은 "한부모"만 탐지한다 - "조손"까지 포함하면
# 손자녀를 양육하는 조부모 세대를 실제로는 다르게 취급해야 할 정책까지 한부모로 잘못 묶일 수 있다.
SINGLE_PARENT_KEYWORDS = ("한부모",)
PREGNANCY_LABEL = "임신 · 출산"


def _parse_categories(value: str | None) -> list[str]:
    if not value:
        return []
    return [c.strip() for c in value.split(",") if c.strip()]


def _both_mentioned(title: str | None, text: str, keywords: tuple[str, ...]) -> bool:
    """키워드가 여러 개일 때(예: 한부모/조손) 제목엔 한쪽 단어, 텍스트엔 다른 쪽 단어만 있는
    "교차 매칭"은 인정하지 않는다 - 같은 단어가 제목과 텍스트 양쪽에 다 나와야 한다."""
    title = title or ""
    return any(k in title and k in text for k in keywords)


def resolve_sbiz(
    trgter_value: str | None,
    life_value: str | None,
    title: str | None,
    target_text: str | None,
    criteria_text: str | None = None,
) -> str | None:
    """sbizCd 문자열(콤마 구분, 여러 카테고리 해당 시) 또는 해당 없으면 None을 반환한다."""
    codes: list[str] = []
    categories = _parse_categories(trgter_value)
    has_structured_tag = bool(categories)
    text = (target_text or "") + " " + (criteria_text or "")

    if "장애인" in categories:
        codes.append(DISABILITY_CODE)
    elif not has_structured_tag and _both_mentioned(title, text, DISABILITY_KEYWORDS):
        codes.append(DISABILITY_CODE)

    if "한부모·조손" in categories:
        codes.append(SINGLE_PARENT_CODE)
    elif not has_structured_tag and _both_mentioned(title, text, SINGLE_PARENT_KEYWORDS):
        codes.append(SINGLE_PARENT_CODE)

    if PREGNANCY_LABEL in _parse_categories(life_value):
        codes.append(WOMAN_CODE)

    return ",".join(codes) if codes else None
