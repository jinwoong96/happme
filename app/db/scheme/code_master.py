from pydantic import BaseModel
from typing import List


class CodeMasterRead(BaseModel):
    code_group: str
    code_value: str
    code_label: str
    sort_order: int

    class Config:
        from_attributes = True


class CodeGroupRead(BaseModel):
    code_group: str
    codes: List[CodeMasterRead]
