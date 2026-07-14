import json
import re
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.core.settings import settings
from app.db.crud.policy import PolicyCrud
from app.db.scheme.policy import PolicyCreate, PolicyUpdate, PolicyRead, PolicyListRead
from app.db.models.policy import Policy
from app.services.ai_client import AiClient

# 정책 카드 표시용 텍스트 길이 제한 (policy_cards.json 원본에 지나치게 긴 값이 섞여있음)
CARD_TITLE_MAX_LENGTH = 60
CARD_SUMMARY_MAX_LENGTH = 150
CARD_TARGET_MAX_LENGTH = 70

_policy_cards_cache: dict[str, dict] | None = None

# 홈 화면 "이번 달 정책 추천" 배너 구성: 지원금액 높은 순 -> 마감임박 순 -> 최신 등록 순으로
# 그룹당 이만큼씩 뽑고, 앞 그룹에서 이미 뽑힌 정책은 뒤 그룹에서 제외해 중복 없이 구성한다.
_BANNER_GROUP_SIZE = 3
# 배너에는 지원금액이 확인된(추출된) 정책만 노출하고, 소액 지원 위주로 보여주기 위해 상한을 둔다.
_BANNER_MAX_SPRT_AMT_LIMIT = 10_000_000
# "마감임박"은 실제로 임박한 것만 보이도록 마감일이 이 안에 드는 정책으로 제한한다.
_BANNER_DEADLINE_WITHIN_DAYS = 30
# 지원금액 높은 순 그룹에서 대분류(lclsfNm)가 겹치지 않게 고르기 위한 후보 풀 크기.
_BANNER_AMOUNT_POOL_SIZE = _BANNER_GROUP_SIZE * 5
# 배너에는 대출/금리혜택성 정책은 지원금 자체가 아니므로 제외한다.
_BANNER_EXCLUDE_KEYWORDS = ["금리혜택", "대출"]

# 가나다순 초성 필터용. 한글 음절의 유니코드 구조(0xAC00 + 초성*588 + 중성*28 + 종성)를 이용해
# 초성 인덱스(0~18: ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ)를 구한 뒤, 된소리(ㄲㄸㅃㅆㅉ)는
# 기본 자음 그룹으로 합쳐서 14개 그룹으로 보여준다.
CONSONANT_GROUPS = ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
_INITIAL_INDEX_TO_GROUP = [0, 0, 1, 2, 2, 3, 4, 5, 5, 6, 6, 7, 8, 8, 9, 10, 11, 12, 13]

# plcySprtCn(지원 내용)에서 "최대 지원 금액"을 뽑아내기 위한 패턴.
# "최대"/"한도"가 금액에 직접 붙어있을 때만 인식해서(예: "최대 100만원", "10만원 한도")
# 오추출 가능성이 있는 애매한 문장(마커 없이 나열된 금액, "최대 12개월"처럼 금액이 아닌
# 값을 수식하는 경우)은 의도적으로 걸러낸다.
_SPRT_UNIT_MULTIPLIER = [
    ("억원", 100_000_000),
    ("백만원", 1_000_000),
    ("만원", 10_000),
    ("원", 1),
]
_SPRT_AMOUNT_UNIT_RE = "|".join(unit for unit, _ in _SPRT_UNIT_MULTIPLIER)
_SPRT_NUMBER_RE = r"[0-9][0-9,\.]*"
_SPRT_MAX_PREFIX_RE = re.compile(rf"최대\s*({_SPRT_NUMBER_RE})\s*({_SPRT_AMOUNT_UNIT_RE})")
_SPRT_LIMIT_SUFFIX_RE = re.compile(rf"({_SPRT_NUMBER_RE})\s*({_SPRT_AMOUNT_UNIT_RE})\s*한도")

# "최대 X"/"X 한도"가 대출/융자의 원금·한도·잔액 그 자체를 가리키는 경우("대출한도: 최대
# 1억원", "대출잔액(최대 1억원)")는 실제로 받는 지원금이 아니라 빌리는 돈의 상한선이라
# 제외한다. "대출이자"/"대출이율"/"대출금리"처럼 이자(비율) 관련 표현은 원금이 아니므로
# 제외 대상에서 뺀다. 매치 직전 구간에서 대출/융자와 금액 사이에 "%"나 "이자"가 끼어있으면
# (예: "대출잔액의 2%, 최대 100만원") 대출잔액을 기준으로 계산된 실제 지원액이라는 뜻이므로
# 제외하지 않는다.
_SPRT_LOAN_PRINCIPAL_RE = re.compile(r"(?:대출|융자)(?!\s*(?:이자|이율|금리))")
_SPRT_LOAN_CONTEXT_WINDOW = 15

# "최대 5억원 대출 지원", "1억원 한도 융자지원"처럼 "대출"/"융자"가 금액 바로 뒤에
# 붙어 지원 대상 자체가 대출/융자임을 밝히는 경우도 대출 원금이라 제외한다. 사이에
# 다른 문장이 끼어있지 않고 공백만 있을 때만 매치되도록(^\s*) 앵커링해서, 관계없는
# 다음 문장/괄호("...최대 50만원) / 융자 추천")까지 잘못 걸리지 않게 한다.
_SPRT_LOAN_AFTER_RE = re.compile(r"^\s*(?:대출|융자)\s*(?:지원|지급)")
_SPRT_LOAN_AFTER_WINDOW = 20

# "최대 X"/"X 한도" 앞쪽에 "본인부담"/"자기부담"이 있으면 본인이 내는 돈일 수 있다("본인부담금
# ... 최대 24,000원" = 본인이 최대 24,000원까지 낸다는 뜻). 다만 뒤에 "지원"/"지급"이 바로
# 따라오면("본인부담금 최대 100만원 지원") 그 부담금을 대신 지원해준다는 뜻이므로 제외하지 않는다.
_SPRT_SELF_PAY_WORDS = ("본인부담", "자기부담")
_SPRT_SELF_PAY_BEFORE_WINDOW = 45
_SPRT_SELF_PAY_AFTER_WINDOW = 15

# 같은 문장 안에서 "기업은"/"기업이"처럼 기업/업체/사업체가 문장의 주어로 쓰이면, 그 문장이
# 서술하는 지원금은 청년 개인이 아니라 그 기업이 받는 돈이라고 본다(예: "기업은 ... 프로그램별
# 최대 50억원까지 지원한다"). 문자 수 제한 없이 문장 경계(마침표 "다."/줄바꿈)까지만 거슬러
# 올라가서 찾기 때문에, 앞 문장의 무관한 "기업" 언급까지 걸리지 않는다. "기업당"/"업체당"처럼
# 자기 사업체를 가리키는 표현(예: "사업화 자금(기업당 최대 4천만원)")은 주어 조사(은/는/이/가)가
# 아니라 부사격 조사라 이 패턴에 걸리지 않는다.
_SPRT_BIZ_SUBJECT_RE = re.compile(r"(?:기업|업체|사업체)(?:은|는|이|가)")

# "소득공제" 문맥의 금액(예: "연 300만원 한도로 40%까지 소득공제 제공")은 실제로 받는
# 지원금이 아니라 세금 계산할 때 빼주는 소득 한도라서 제외한다. 같은 문장/줄 안에서만
# 확인해서(마침표 "다."/줄바꿈이 경계) 다른 문장의 무관한 "소득공제" 언급까지 걸리지
# 않게 한다.
_SPRT_INCOME_DEDUCTION_WORD = "소득공제"


class PolicyService:

    @staticmethod
    async def _require_policy(db: AsyncSession, policy_id: int) -> Policy:
        policy = await PolicyCrud.get_policy(db, policy_id)
        if not policy:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"policy_id '{policy_id}'에 해당하는 정책이 없습니다.")
        return policy

    @staticmethod
    async def create_policy_svc(db: AsyncSession, data: PolicyCreate) -> Policy:
        try:
            policy = await PolicyCrud.create_policy(db, data)
            await db.commit()
            await db.refresh(policy)
            return policy
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="정책 생성에 실패했습니다.")

    @staticmethod
    async def get_policy_svc(db: AsyncSession, policy_id: int) -> dict:
        policy = await PolicyService._require_policy(db, policy_id)
        await PolicyCrud.increment_inq_cnt(db, policy)
        await db.commit()
        await db.refresh(policy)

        item = PolicyRead.model_validate(policy).model_dump()
        if policy.plcyNo:
            cards = await PolicyService.get_policy_cards_svc(db, [policy.plcyNo])
            card = cards.get(policy.plcyNo)
            if card:
                item["policy_summary"] = card.get("policy_summary")
                item["apply_period_type"] = card.get("apply_period_type")
                item["apply_period"] = card.get("apply_period")
                item["target"] = card.get("target")
        return item

    @staticmethod
    async def get_all_policies_svc(
        db: AsyncSession,
        age: Optional[int] = None,
        region: Optional[str] = None,
        lclsf: Optional[str] = None,
        mclsf: Optional[str] = None,
        keyword: Optional[str] = None,
        sort: Optional[str] = None,
        include_closed: bool = False,
        consonant: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        policies = await PolicyCrud.get_all_policies(
            db, age=age, region=region, lclsf=lclsf, mclsf=mclsf, keyword=keyword, sort=sort,
            include_closed=include_closed, consonant=consonant, limit=limit, offset=offset,
        )

        if consonant:
            policies = PolicyService._filter_by_consonant(policies, consonant)[offset:offset + limit]

        plcy_nos = [p.plcyNo for p in policies if p.plcyNo]
        cards = await PolicyService.get_policy_cards_svc(db, plcy_nos)

        results = []
        for p in policies:
            item = PolicyListRead.model_validate(p).model_dump()
            card = cards.get(p.plcyNo) if p.plcyNo else None
            if card:
                item["policy_summary"] = card.get("policy_summary")
                item["apply_period_type"] = card.get("apply_period_type")
                item["apply_period"] = card.get("apply_period")
                item["target"] = card.get("target")
            results.append(item)
        return results

    @staticmethod
    def _pick_diverse_by_category(policies: list[Policy], count: int, seen_categories: set) -> list[Policy]:
        """대분류(lclsfNm)가 최대한 겹치지 않게 순위 순으로 고르고, 종류가 모자라면 순위 순으로 채운다.
        seen_categories는 호출 간에 공유되는 집합으로, 이미 고른 카테고리를 계속 누적한다."""
        selected: list[Policy] = []
        leftover: list[Policy] = []
        for p in policies:
            if len(selected) == count:
                break
            if p.lclsfNm not in seen_categories:
                selected.append(p)
                seen_categories.add(p.lclsfNm)
            else:
                leftover.append(p)
        if len(selected) < count:
            selected.extend(leftover[: count - len(selected)])
        return selected

    @staticmethod
    async def get_home_banner_svc(db: AsyncSession) -> list[dict]:
        """
        홈 화면 "이번 달 정책 추천" 배너용. 지원금액 높은 순/마감임박 순/최신 등록 순으로
        각각 몇 개씩 뽑되, 앞에서 이미 뽑힌 정책은 뒤 그룹에서 제외해 중복 없이 구성한다.
        마감임박은 실제로 30일 이내인 것만 인정하고, 그만큼 부족해진 개수는 지원금액 높은
        순으로 채운다.
        """
        exclude_ids: list[int] = []
        exclude_names: list[str] = []
        selected: list[tuple[str, Policy]] = []

        amount_seen_categories: set = set()

        async def fetch_amount(count: int) -> list[Policy]:
            pool = await PolicyCrud.get_all_policies(
                db, sort="amount", include_closed=False, exclude_ids=exclude_ids,
                exclude_names=exclude_names, max_sprt_amt_not_null=True,
                max_sprt_amt_below=_BANNER_MAX_SPRT_AMT_LIMIT,
                exclude_keywords=_BANNER_EXCLUDE_KEYWORDS,
                limit=max(count * 5, _BANNER_AMOUNT_POOL_SIZE),
            )
            return PolicyService._pick_diverse_by_category(pool, count, amount_seen_categories)

        amount_policies = await fetch_amount(_BANNER_GROUP_SIZE)
        exclude_ids.extend(p.policy_id for p in amount_policies)
        exclude_names.extend(p.plcyNm for p in amount_policies)
        selected.extend(("amount", p) for p in amount_policies)

        deadline_policies = await PolicyCrud.get_all_policies(
            db, sort="deadline", include_closed=False, exclude_ids=exclude_ids,
            exclude_names=exclude_names, max_sprt_amt_not_null=True,
            max_sprt_amt_below=_BANNER_MAX_SPRT_AMT_LIMIT,
            deadline_within_days=_BANNER_DEADLINE_WITHIN_DAYS,
            exclude_keywords=_BANNER_EXCLUDE_KEYWORDS, limit=_BANNER_GROUP_SIZE,
        )
        exclude_ids.extend(p.policy_id for p in deadline_policies)
        exclude_names.extend(p.plcyNm for p in deadline_policies)
        selected.extend(("deadline", p) for p in deadline_policies)

        shortfall = _BANNER_GROUP_SIZE - len(deadline_policies)
        if shortfall > 0:
            backfill = await fetch_amount(shortfall)
            exclude_ids.extend(p.policy_id for p in backfill)
            exclude_names.extend(p.plcyNm for p in backfill)
            selected.extend(("amount", p) for p in backfill)

        latest_policies = await PolicyCrud.get_all_policies(
            db, sort="latest", include_closed=False, exclude_ids=exclude_ids,
            exclude_names=exclude_names, max_sprt_amt_not_null=True,
            max_sprt_amt_below=_BANNER_MAX_SPRT_AMT_LIMIT,
            exclude_keywords=_BANNER_EXCLUDE_KEYWORDS, limit=_BANNER_GROUP_SIZE,
        )
        exclude_ids.extend(p.policy_id for p in latest_policies)
        exclude_names.extend(p.plcyNm for p in latest_policies)
        selected.extend(("latest", p) for p in latest_policies)

        plcy_nos = [p.plcyNo for _, p in selected if p.plcyNo]
        cards = await PolicyService.get_policy_cards_svc(db, plcy_nos)

        results = []
        for reason, p in selected:
            item = PolicyListRead.model_validate(p).model_dump()
            card = cards.get(p.plcyNo) if p.plcyNo else None
            if card:
                item["policy_summary"] = card.get("policy_summary")
                item["apply_period_type"] = card.get("apply_period_type")
                item["apply_period"] = card.get("apply_period")
                item["target"] = card.get("target")
            item["banner_reason"] = reason
            results.append(item)
        return results

    @staticmethod
    def _initial_consonant_group(plcy_nm: Optional[str]) -> str:
        """plcyNm 첫 글자의 초성 그룹(ㄱ~ㅎ 14종)을 구한다. 한글 음절이 아니면 '기타'."""
        if not plcy_nm:
            return "기타"
        code = ord(plcy_nm[0])
        if 0xAC00 <= code <= 0xD7A3:
            initial_index = (code - 0xAC00) // 588
            return CONSONANT_GROUPS[_INITIAL_INDEX_TO_GROUP[initial_index]]
        return "기타"

    @staticmethod
    def _filter_by_consonant(policies: list[Policy], consonant: str) -> list[Policy]:
        return [p for p in policies if PolicyService._initial_consonant_group(p.plcyNm) == consonant]

    @staticmethod
    def _sprt_amount_to_won(amount_str: str, unit: str) -> Optional[int]:
        try:
            value = float(amount_str.replace(",", ""))
        except ValueError:
            return None
        for u, multiplier in _SPRT_UNIT_MULTIPLIER:
            if unit == u:
                return round(value * multiplier)
        return None

    @staticmethod
    def _is_loan_principal_context(text: str, match_start: int) -> bool:
        """
        매치 직전 구간에 "대출"/"융자"(이자·이율·금리 표현 제외)가 있고, 그 뒤부터 매치
        시작까지 사이에 "%"나 "이자"가 없으면 대출 원금/한도/잔액 자체를 가리키는 것으로
        본다(예: "대출한도 : 최대 1억원", "대출잔액(최대 1억원)").
        """
        start = max(0, match_start - _SPRT_LOAN_CONTEXT_WINDOW)
        context = text[start:match_start]
        last_end = -1
        for m in _SPRT_LOAN_PRINCIPAL_RE.finditer(context):
            last_end = max(last_end, m.end())
        if last_end == -1:
            return False
        between = context[last_end:]
        return "%" not in between and "이자" not in between

    @staticmethod
    def _is_loan_principal_after_context(text: str, match_end: int) -> bool:
        """
        매치 바로 뒤(공백만 허용)에 "대출"/"융자" + "지원"/"지급"이 곧바로 이어지면
        ("최대 5억원 대출 지원", "1억원 한도 융자지원") 지원 대상 자체가 대출/융자
        원금이라는 뜻이므로 제외한다. 문장이 끝나거나(괄호/줄바꿈 등) 다른 내용이
        끼어있으면 매치하지 않아, 관계없는 다음 문장까지 잘못 걸리지 않게 한다.
        """
        after = text[match_end:match_end + _SPRT_LOAN_AFTER_WINDOW]
        return bool(_SPRT_LOAN_AFTER_RE.match(after))

    @staticmethod
    def _is_self_payment_context(text: str, match_start: int, match_end: int) -> bool:
        """
        매치 앞쪽(넓은 구간)에 "본인부담"/"자기부담"이 있으면 본인이 내는 돈일 가능성이
        있다고 보되, 매치 바로 뒤에 "지원"/"지급"이 오면("본인부담금 최대 100만원 지원")
        그 부담금을 대신 지원해준다는 뜻이므로 제외하지 않는다.
        """
        before = text[max(0, match_start - _SPRT_SELF_PAY_BEFORE_WINDOW):match_start]
        if not any(word in before for word in _SPRT_SELF_PAY_WORDS):
            return False
        after = text[match_end:match_end + _SPRT_SELF_PAY_AFTER_WINDOW]
        return not ("지원" in after or "지급" in after)

    @staticmethod
    def _is_business_subject_context(text: str, match_start: int) -> bool:
        """
        매치가 속한 문장 안에서 "기업은"/"기업이"처럼 기업/업체/사업체가 문장의 주어로
        쓰였으면, 그 문장이 서술하는 지원금은 그 기업이 받는 돈이라고 본다. 문장 경계
        (마침표 "다."/줄바꿈)까지만 거슬러 올라가서 찾으므로 앞 문장의 무관한 "기업"
        언급까지 걸리지 않는다.
        """
        before = text[:match_start]
        cut = max(before.rfind("다."), before.rfind("\n"))
        scoped = before[cut + 1:] if cut != -1 else before
        return bool(_SPRT_BIZ_SUBJECT_RE.search(scoped))

    @staticmethod
    def _is_income_deduction_context(text: str, match_start: int, match_end: int) -> bool:
        """
        매치가 속한 문장/줄 안에 "소득공제"가 있으면(예: "연 300만원 한도로 40%까지
        소득공제 제공") 실제 지원금이 아니라 세제 혜택 한도이므로 제외한다. "소득공제"는
        금액 앞/뒤 어느 쪽에도 올 수 있어 문장 경계(마침표 "다."/줄바꿈)까지 양쪽 다 살핀다.
        """
        before_cut = max(text.rfind("다.", 0, match_start), text.rfind("\n", 0, match_start))
        start = before_cut + 1 if before_cut != -1 else 0
        after_dot = text.find("다.", match_end)
        after_nl = text.find("\n", match_end)
        boundaries = [b for b in (after_dot, after_nl) if b != -1]
        end = min(boundaries) if boundaries else len(text)
        return _SPRT_INCOME_DEDUCTION_WORD in text[start:end]

    @staticmethod
    def extract_max_support_amount(plcy_sprt_cn: Optional[str]) -> Optional[int]:
        """
        plcySprtCn(지원 내용) 텍스트에서 "최대 지원 금액"(원)을 뽑아낸다. "최대 100만원",
        "10만원 한도"처럼 마커가 금액에 직접 붙어있을 때만 인식하고, 후보가 여러 개면
        그중 최댓값을 쓴다. 마커 없이 나열된 금액, 대출 원금/한도 자체를 가리키는 금액,
        지원 없이 본인이 부담하는 금액은 오추출 방지를 위해 무시하고 None을 반환한다.
        """
        if not plcy_sprt_cn:
            return None

        candidates = []
        for pattern in (_SPRT_MAX_PREFIX_RE, _SPRT_LIMIT_SUFFIX_RE):
            for m in pattern.finditer(plcy_sprt_cn):
                if PolicyService._is_loan_principal_context(plcy_sprt_cn, m.start()):
                    continue
                if PolicyService._is_loan_principal_after_context(plcy_sprt_cn, m.end()):
                    continue
                if PolicyService._is_self_payment_context(plcy_sprt_cn, m.start(), m.end()):
                    continue
                if PolicyService._is_business_subject_context(plcy_sprt_cn, m.start()):
                    continue
                if PolicyService._is_income_deduction_context(plcy_sprt_cn, m.start(), m.end()):
                    continue
                won = PolicyService._sprt_amount_to_won(m.group(1), m.group(2))
                if won is not None:
                    candidates.append(won)

        return max(candidates) if candidates else None

    @staticmethod
    async def update_policy_svc(db: AsyncSession, policy_id: int, data: PolicyUpdate) -> Policy:
        policy = await PolicyService._require_policy(db, policy_id)
        try:
            updated = await PolicyCrud.update_policy(db, policy, data)
            await db.commit()
            await db.refresh(updated)
            return updated
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="정책 수정에 실패했습니다.")

    @staticmethod
    async def delete_policy_svc(db: AsyncSession, policy_id: int) -> dict:
        policy = await PolicyService._require_policy(db, policy_id)
        try:
            await PolicyCrud.delete_policy(db, policy)
            await db.commit()
            return {"message": f"policy_id '{policy_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="정책 삭제에 실패했습니다.")

    @staticmethod
    async def similarity_search_svc(db: AsyncSession, query_text: str, top_k: int = 5) -> list[dict]:
        """bene_ai(BAAI/bge-m3 임베딩)로 유사 정책을 검색한 뒤, plcyNo -> 실제 DB row(Policy)로 매핑한다."""
        matches = await AiClient.search_similar_policies(query_text, top_k=top_k)

        plcy_nos = [m["plcyNo"] for m in matches if m.get("plcyNo")]
        id_map = await PolicyCrud.get_policy_ids_by_plcyno(db, plcy_nos)
        policies = await PolicyCrud.get_policies_by_ids(db, list(id_map.values()))
        policies_by_id = {p.policy_id: p for p in policies}

        results = []
        for m in matches:
            plcy_no = m.get("plcyNo")
            policy_id = id_map.get(plcy_no) if plcy_no else None
            policy = policies_by_id.get(policy_id) if policy_id else None
            if policy:
                results.append({"policy": policy, "score": m["score"]})
        return results

    @staticmethod
    async def get_category_list_svc(db: AsyncSession) -> list[str]:
        return await PolicyCrud.get_distinct_mclsf(db)

    @staticmethod
    async def add_region_svc(db: AsyncSession, policy_id: int, zip_code: str) -> dict:
        await PolicyService._require_policy(db, policy_id)
        try:
            await PolicyCrud.add_region(db, policy_id, zip_code)
            await db.commit()
            return {"message": f"지역 코드 '{zip_code}' 추가 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="지역 추가에 실패했습니다.")

    @staticmethod
    async def get_policy_cards_svc(db: AsyncSession, plcy_nos: list[str]) -> dict[str, dict]:
        """
        plcyNo -> 정책 카드 표시용 필드(policy_name/policy_summary/apply_period_type/apply_period/target/link).
        지금은 policy_cards.json(임시 파일)에서 읽지만, 추후 policy 테이블에 컬럼이 추가되면
        이 함수 내부만 DB 조회로 바꾸면 됩니다(호출부는 변경 없음).
        """
        cards = PolicyService._load_policy_cards()
        return {
            plcy_no: PolicyService._to_display_card(cards[plcy_no])
            for plcy_no in plcy_nos
            if plcy_no in cards
        }

    @staticmethod
    def _load_policy_cards() -> dict[str, dict]:
        global _policy_cards_cache
        if _policy_cards_cache is None:
            with open(settings.policy_cards_path, encoding="utf-8") as f:
                cards = json.load(f)
            _policy_cards_cache = {str(c.get("plcyNo")): c for c in cards}
        return _policy_cards_cache

    @staticmethod
    def _truncate(text: Optional[str], max_length: int) -> Optional[str]:
        if not text or len(text) <= max_length:
            return text
        return text[:max_length].rstrip() + "..."

    @staticmethod
    def _clean_target(text: Optional[str]) -> Optional[str]:
        """
        target은 '나이 | 소득조건 | 세부요건' 을 |로 이어붙인 값인데, 뒤쪽 항목이 비어있으면
        '만 34~99세 | -' 처럼 의미 없는 조각이 그대로 남아있습니다. 그런 조각은 걸러냅니다.
        """
        if not text:
            return None
        parts = [p.strip() for p in text.split("|")]
        meaningful = [p for p in parts if p and p != "-"]
        return " | ".join(meaningful) if meaningful else None

    @staticmethod
    def _to_display_card(card: dict) -> dict:
        return {
            "policy_name": PolicyService._truncate(card.get("title"), CARD_TITLE_MAX_LENGTH),
            "policy_summary": PolicyService._truncate(card.get("support_summary"), CARD_SUMMARY_MAX_LENGTH),
            "apply_period_type": card.get("apply_period_type"),
            "apply_period": card.get("apply_period"),
            "target": PolicyService._truncate(PolicyService._clean_target(card.get("target")), CARD_TARGET_MAX_LENGTH),
            "link": card.get("link"),
        }
