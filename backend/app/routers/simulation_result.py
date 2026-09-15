from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.db.scheme.simulation_result import SimulationResultCreate, SimulationResultRead
from app.db.models.user import User
from app.services.simulation_result import SimulationResultService as sim_svc
from app.core.jwt_handle import get_current_user

router = APIRouter(prefix="/simulations", tags=["SimulationResult"])


# C 생성
@router.post("/", response_model=SimulationResultRead, status_code=201)
async def create_result(data: SimulationResultCreate, db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await sim_svc.create_result_svc(db, data)


# R 내 시뮬레이션 목록
@router.get("/me", response_model=list[SimulationResultRead])
async def get_my_results(db: AsyncSession = Depends(get_db), current_user: User = Depends(get_current_user)):
    return await sim_svc.get_by_user_svc(db, current_user.user_id)


# R 단일 조회
@router.get("/{result_id}", response_model=SimulationResultRead)
async def get_result(result_id: int, db: AsyncSession = Depends(get_db)):
    return await sim_svc.get_result_svc(db, result_id)


# D 삭제
@router.delete("/{result_id}")
async def delete_result(result_id: int, db: AsyncSession = Depends(get_db)):
    return await sim_svc.delete_result_svc(db, result_id)
