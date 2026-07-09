import json
import re
from datetime import date
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.core.settings import settings
from app.db.crud.policy import PolicyCrud
from app.db.scheme.policy import PolicyCreate, PolicyUpdate, PolicyListRead
from app.db.models.policy import Policy

_APLY_YMD_DATE_RE = re.compile(r"(\d{4})[.\-/]?(\d{2})[.\-/]?(\d{2})")

# 정책 카드 표시용 텍스트 길이 제한 (policy_cards.json 원본에 지나치게 긴 값이 섞여있음)
CARD_TITLE_MAX_LENGTH = 60
CARD_SUMMARY_MAX_LENGTH = 150
CARD_TARGET_MAX_LENGTH = 70

_policy_cards_cache: dict[str, dict] | None = None


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
        limit: int = 20,
        offset: int = 0,
    ) -> list[dict]:
        policies = await PolicyCrud.get_all_policies(db, age=age, region=region, lclsf=lclsf, keyword=keyword, sort=sort, limit=limit, offset=offset)

        if sort == "deadline":
            policies = PolicyService._sort_by_deadline(policies)[offset:offset + limit]

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
    def _parse_aply_end_date(aply_ymd: Optional[str]) -> Optional[date]:
        """
        aplyYmd(예: "20250301 ~ 20251231", "2025.03.01 ~ 2025.12.31")에서 마감일을 뽑아낸다.
        "상시"처럼 날짜 두 개를 못 찾으면 None(마감일 없음).
        """
        if not aply_ymd:
            return None
        dates = _APLY_YMD_DATE_RE.findall(aply_ymd)
        if len(dates) < 2:
            return None
        year, month, day = dates[1]
        try:
            return date(int(year), int(month), int(day))
        except ValueError:
            return None

    @staticmethod
    def _sort_by_deadline(policies: list[Policy]) -> list[Policy]:
        """
        아직 마감되지 않은 정책 중 마감일이 가까운(=오늘에서 가까운 미래) 순으로 앞에 오게 정렬한다.
        이미 마감이 지난 정책은 "임박"이 아니므로 그 뒤로(최근에 마감된 것부터), 마감일을
        알 수 없는 정책(상시 등)은 맨 뒤로 보낸다.
        """
        today = date.today()

        def sort_key(p: Policy):
            end_date = PolicyService._parse_aply_end_date(p.aplyYmd)
            if end_date is None:
                return (2, 0)
            if end_date < today:
                return (1, -end_date.toordinal())
            return (0, end_date.toordinal())

        return sorted(policies, key=sort_key)

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
