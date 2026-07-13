import json
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.core.settings import settings
from app.db.crud.policy import PolicyCrud
from app.db.scheme.policy import PolicyCreate, PolicyUpdate, PolicyListRead
from app.db.models.policy import Policy
from app.services.ai_client import AiClient

# 정책 카드 표시용 텍스트 길이 제한 (policy_cards.json 원본에 지나치게 긴 값이 섞여있음)
CARD_TITLE_MAX_LENGTH = 60
CARD_SUMMARY_MAX_LENGTH = 150
CARD_TARGET_MAX_LENGTH = 70

_policy_cards_cache: dict[str, dict] | None = None

# 가나다순 초성 필터용. 한글 음절의 유니코드 구조(0xAC00 + 초성*588 + 중성*28 + 종성)를 이용해
# 초성 인덱스(0~18: ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ)를 구한 뒤, 된소리(ㄲㄸㅃㅆㅉ)는
# 기본 자음 그룹으로 합쳐서 14개 그룹으로 보여준다.
CONSONANT_GROUPS = ["ㄱ", "ㄴ", "ㄷ", "ㄹ", "ㅁ", "ㅂ", "ㅅ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]
_INITIAL_INDEX_TO_GROUP = [0, 0, 1, 2, 2, 3, 4, 5, 5, 6, 6, 7, 8, 8, 9, 10, 11, 12, 13]


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
    async def get_policy_svc(db: AsyncSession, policy_id: int) -> Policy:
        policy = await PolicyService._require_policy(db, policy_id)
        await PolicyCrud.increment_inq_cnt(db, policy)
        await db.commit()
        await db.refresh(policy)
        return policy

    @staticmethod
    async def get_all_policies_svc(
        db: AsyncSession,
        age: Optional[int] = None,
        region: Optional[str] = None,
        lclsf: Optional[str] = None,
        keyword: Optional[str] = None,
        sort: Optional[str] = None,
        include_closed: bool = False,
        consonant: Optional[str] = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        policies = await PolicyCrud.get_all_policies(
            db, age=age, region=region, lclsf=lclsf, keyword=keyword, sort=sort, include_closed=include_closed,
            consonant=consonant, limit=limit, offset=offset,
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
