from app.db.database import Base
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy import String, Boolean, DateTime, Integer, func, text
from datetime import datetime
from typing import Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from .user_profile import UserProfile
    from .bookmark import Bookmark
    from .notification import Notification
    from .inquiry import Inquiry
    from .ad_partnership_inquiry import AdPartnershipInquiry
    from .corporate_support_inquiry import CorporateSupportInquiry
    from .notice import Notice
    from .simulation_result import SimulationResult
    from .user_testprofile import UserTestProfile
    from .ocr_result import OcrResult
    from .pdf_summary import PdfSummary
    from .user_alert_keyword import UserAlertKeyword


class User(Base):
    __tablename__ = "user"

    user_id:           Mapped[int]            = mapped_column(Integer, primary_key=True, autoincrement=True)
    name:              Mapped[Optional[str]]  = mapped_column(String(100), nullable=True)
    email:             Mapped[Optional[str]]  = mapped_column(String(100), unique=True, nullable=True)
    provider:          Mapped[str]            = mapped_column(String(20), nullable=False, server_default=text("'local'"))
    password:          Mapped[Optional[str]]  = mapped_column(String(255), nullable=True)
    role:              Mapped[str]            = mapped_column(String(20), nullable=False, server_default=text("'USER'"))
    profile_completed: Mapped[bool]           = mapped_column(Boolean, nullable=False, server_default=text("0"))
    refresh_token:     Mapped[Optional[str]]  = mapped_column(String(512), nullable=True)
    created_at:        Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), nullable=True)
    updated_at:        Mapped[Optional[datetime]] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now(), nullable=True)

    profile:            Mapped[Optional["UserProfile"]]       = relationship("UserProfile", back_populates="user", uselist=False, cascade="all, delete-orphan")
    bookmarks:          Mapped[List["Bookmark"]]              = relationship("Bookmark", back_populates="user", cascade="all, delete-orphan")
    notifications:      Mapped[List["Notification"]]          = relationship("Notification", back_populates="user", cascade="all, delete-orphan")
    inquiries:          Mapped[List["Inquiry"]]               = relationship("Inquiry", back_populates="user", cascade="all, delete-orphan")
    ad_partnership_inquiries:      Mapped[List["AdPartnershipInquiry"]]      = relationship("AdPartnershipInquiry", back_populates="user", cascade="all, delete-orphan")
    corporate_support_inquiries:   Mapped[List["CorporateSupportInquiry"]]   = relationship("CorporateSupportInquiry", back_populates="user", cascade="all, delete-orphan")
    notices:            Mapped[List["Notice"]]                = relationship("Notice", back_populates="admin", cascade="all, delete-orphan")
    simulation_results: Mapped[List["SimulationResult"]]      = relationship("SimulationResult", back_populates="user", cascade="all, delete-orphan")
    test_profiles:      Mapped[List["UserTestProfile"]]       = relationship("UserTestProfile", back_populates="user", cascade="all, delete-orphan")
    ocr_results:        Mapped[List["OcrResult"]]             = relationship("OcrResult", back_populates="user", cascade="all, delete-orphan")
    pdf_summaries:      Mapped[List["PdfSummary"]]            = relationship("PdfSummary", back_populates="user", cascade="all, delete-orphan")
    alert_keywords:     Mapped[List["UserAlertKeyword"]]      = relationship("UserAlertKeyword", back_populates="user", cascade="all, delete-orphan")
