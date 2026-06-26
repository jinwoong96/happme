from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer


class CodeMaster(Base):
    __tablename__ = "code_master"

    code_group: Mapped[str] = mapped_column(String(50), primary_key=True)
    code_value: Mapped[str] = mapped_column(String(50), primary_key=True)
    code_label: Mapped[str] = mapped_column(String(100), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0)
