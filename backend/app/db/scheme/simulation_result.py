from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class SimulationResultCreate(BaseModel):
    user_id: int
    policy_id: int
    simulation_input: dict


class SimulationResultRead(BaseModel):
    result_id: int
    user_id: int
    policy_id: int
    simulation_input: dict
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True
