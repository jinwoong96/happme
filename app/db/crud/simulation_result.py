from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.models.simulation_result import SimulationResult
from app.db.scheme.simulation_result import SimulationResultCreate


class SimulationResultCrud:

    @staticmethod
    async def create_result(db: AsyncSession, data: SimulationResultCreate) -> SimulationResult:
        result = SimulationResult(**data.model_dump())
        db.add(result)
        await db.flush()
        return result

    @staticmethod
    async def get_result(db: AsyncSession, result_id: int) -> SimulationResult | None:
        result = await db.execute(select(SimulationResult).where(SimulationResult.result_id == result_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_user(db: AsyncSession, user_id: int) -> list[SimulationResult]:
        result = await db.execute(
            select(SimulationResult).where(SimulationResult.user_id == user_id).order_by(SimulationResult.created_at.desc())
        )
        return list(result.scalars().all())

    @staticmethod
    async def delete_result(db: AsyncSession, sim_result: SimulationResult) -> None:
        await db.delete(sim_result)
        await db.flush()
