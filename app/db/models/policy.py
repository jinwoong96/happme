from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Text, Integer, BigInteger, DateTime, Date, func
from datetime import datetime, date
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .policy_region import PolicyRegion
    from .bookmark import Bookmark
    from .notification import Notification
    from .simulation_result import SimulationResult
    from .ocr_result import OcrResultMatch
    from .pdf_summary import PdfSummaryMatch
    from .policy_schedule_event import PolicyScheduleEvent
    from .policy_ai_tip import PolicyAiTip
    from .policy_income_required import PolicyIncomeRequired


class Policy(Base):
    __tablename__ = "policy"

    policy_id:       Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    plcyNo:          Mapped[Optional[str]]  = mapped_column(String(50), unique=True, nullable=True)
    plcyNm:          Mapped[str]            = mapped_column(String(255), nullable=False)
    plcyKywdNm:      Mapped[str]            = mapped_column(String(255), nullable=False)
    plcyExplnCn:     Mapped[str]            = mapped_column(Text, nullable=False)
    lclsfNm:         Mapped[str]            = mapped_column(String(100), nullable=False)
    mclsfNm:         Mapped[str]            = mapped_column(String(100), nullable=False)
    plcySprtCn:      Mapped[str]            = mapped_column(Text, nullable=False)
    sprvsnInstCdNm:  Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
    sprvsnInstPicNm: Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)
    operInstCdNm:    Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
    operInstPicNm:   Mapped[Optional[str]]  = mapped_column(String(50), nullable=True)
    bizPrdBgngYmd:   Mapped[Optional[str]]  = mapped_column(String(20), nullable=True)
    bizPrdEndYmd:    Mapped[Optional[str]]  = mapped_column(String(20), nullable=True)
    bizPrdEtcCn:     Mapped[Optional[str]]  = mapped_column(String(255), nullable=True)
    plcyAplyMthdCn:  Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    srngMthdCn:      Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    aplyUrlAddr:     Mapped[Optional[str]]  = mapped_column(String(500), nullable=True)
    sbmsnDcmntCn:    Mapped[str]            = mapped_column(Text, nullable=False)
    aplyYmd:         Mapped[str]            = mapped_column(String(100), nullable=False)
    aplyEndDt:       Mapped[Optional[date]] = mapped_column(Date, nullable=True)  # aplyYmd("YYYYMMDD ~ YYYYMMDD")에서 뽑아낸 마감일. 파싱 불가(상시 등)면 NULL
    refUrlAddr1:     Mapped[Optional[str]]  = mapped_column(String(500), nullable=True)
    refUrlAddr2:     Mapped[Optional[str]]  = mapped_column(String(500), nullable=True)
    etcMttrCn:       Mapped[Optional[str]]  = mapped_column(Text, nullable=True)
    sprtSclCnt:      Mapped[Optional[int]]  = mapped_column(Integer, nullable=True)
    sprtTrgtMinAge:  Mapped[int]            = mapped_column(Integer, nullable=False)
    sprtTrgtMaxAge:  Mapped[int]            = mapped_column(Integer, nullable=False)
    earnMinAmt:      Mapped[Optional[int]]  = mapped_column(BigInteger, nullable=True)
    earnMaxAmt:      Mapped[Optional[int]]  = mapped_column(BigInteger, nullable=True)
    earnEtcCn:       Mapped[str]            = mapped_column(Text, nullable=False)
    earnCndSeCd:     Mapped[Optional[str]]  = mapped_column(String(20), nullable=True)
    addAplyQlfcCndCn: Mapped[str]           = mapped_column(Text, nullable=False)
    ptcpPrpTrgtCn:   Mapped[str]           = mapped_column(Text, nullable=False)
    mrgSttsCd:       Mapped[Optional[str]]  = mapped_column(String(20), nullable=True)
    inqCnt:          Mapped[int]            = mapped_column(Integer, nullable=False, default=0)
    bookmarkCnt:     Mapped[int]            = mapped_column(Integer, nullable=False, default=0)
    frstRegDt:       Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    lastMdfcnDt:     Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)
    createdAt:       Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)
    updatedAt:       Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    regions:            Mapped[List["PolicyRegion"]]     = relationship("PolicyRegion", back_populates="policy", cascade="all, delete-orphan")
    bookmarks:          Mapped[List["Bookmark"]]         = relationship("Bookmark", back_populates="policy", cascade="all, delete-orphan")
    notifications:      Mapped[List["Notification"]]     = relationship("Notification", back_populates="policy")
    simulation_results: Mapped[List["SimulationResult"]] = relationship("SimulationResult", back_populates="policy", cascade="all, delete-orphan")
    ocr_matches:        Mapped[List["OcrResultMatch"]]   = relationship("OcrResultMatch", back_populates="policy")
    pdf_matches:        Mapped[List["PdfSummaryMatch"]]  = relationship("PdfSummaryMatch", back_populates="policy")
    schedule_events:    Mapped[List["PolicyScheduleEvent"]] = relationship("PolicyScheduleEvent", back_populates="policy", cascade="all, delete-orphan")
    ai_tip:             Mapped[Optional["PolicyAiTip"]]   = relationship("PolicyAiTip", back_populates="policy", uselist=False, cascade="all, delete-orphan")
    income_required:    Mapped[Optional["PolicyIncomeRequired"]] = relationship("PolicyIncomeRequired", back_populates="policy", uselist=False, cascade="all, delete-orphan")
