from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status
from app.db.crud.simulation_result import SimulationResultCrud
from app.db.crud.user import UserCrud
from app.db.crud.policy import PolicyCrud
from app.db.scheme.simulation_result import SimulationResultCreate
from app.db.models.simulation_result import SimulationResult


class SimulationResultService:

    @staticmethod
    async def create_result_svc(db: AsyncSession, data: SimulationResultCreate) -> SimulationResult:
        if not await UserCrud.get_user(db, data.user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        if not await PolicyCrud.get_policy(db, data.policy_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="정책을 찾을 수 없습니다.")
        try:
            result = await SimulationResultCrud.create_result(db, data)
            await db.commit()
            await db.refresh(result)
            return result
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="시뮬레이션 결과 저장에 실패했습니다.")

    @staticmethod
    async def get_result_svc(db: AsyncSession, result_id: int) -> SimulationResult:
        result = await SimulationResultCrud.get_result(db, result_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="시뮬레이션 결과를 찾을 수 없습니다.")
        return result

    @staticmethod
    async def get_by_user_svc(db: AsyncSession, user_id: int) -> list[SimulationResult]:
        if not await UserCrud.get_user(db, user_id):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="유저를 찾을 수 없습니다.")
        return await SimulationResultCrud.get_by_user(db, user_id)

    @staticmethod
    async def delete_result_svc(db: AsyncSession, result_id: int) -> dict:
        result = await SimulationResultCrud.get_result(db, result_id)
        if not result:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="시뮬레이션 결과를 찾을 수 없습니다.")
        try:
            await SimulationResultCrud.delete_result(db, result)
            await db.commit()
            return {"message": f"result_id '{result_id}' 삭제 완료"}
        except Exception:
            await db.rollback()
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="시뮬레이션 결과 삭제에 실패했습니다.")
