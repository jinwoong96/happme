from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.policy import PolicyCrud
from app.db.scheme.policy import PolicyCreate, PolicyUpdate
from app.db.models.policy import Policy


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
        limit: int = 20,
        offset: int = 0,
    ) -> list[Policy]:
        return await PolicyCrud.get_all_policies(db, age=age, region=region, lclsf=lclsf, keyword=keyword, limit=limit, offset=offset)

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
