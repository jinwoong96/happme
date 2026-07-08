from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, Numeric


class LocalProgram(Base):
    __tablename__ = "local_program"

    local_program_id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    svcid: Mapped[str] = mapped_column(String(50), unique=True)
    svcnm: Mapped[str] = mapped_column(String(255))
    svcstatnm: Mapped[str | None] = mapped_column(String(50))
    usetgtinfo: Mapped[str | None] = mapped_column(String(255))
    gubun: Mapped[str | None] = mapped_column(String(50))
    minclassnm: Mapped[str | None] = mapped_column(String(100))
    maxclassnm: Mapped[str | None] = mapped_column(String(100))
    payatnm: Mapped[str | None] = mapped_column(String(50))
    svcurl: Mapped[str | None] = mapped_column(String(500))
    placenm: Mapped[str | None] = mapped_column(String(255))
    areanm: Mapped[str | None] = mapped_column(String(50))
    rcptbgndt: Mapped[object | None] = mapped_column(DateTime)
    rcptenddt: Mapped[object | None] = mapped_column(DateTime)
    svcopnbgndt: Mapped[object | None] = mapped_column(DateTime)
    svcopnenddt: Mapped[object | None] = mapped_column(DateTime)
    latitude: Mapped[float | None] = mapped_column(Numeric(10, 8))
    longitude: Mapped[float | None] = mapped_column(Numeric(11, 8))
    createdAt: Mapped[object | None] = mapped_column(DateTime)
    updatedAt: Mapped[object | None] = mapped_column(DateTime)
