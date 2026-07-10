from sqlalchemy import Column, Integer, String, Text, DateTime
from sqlalchemy.sql import func
from app.db.database import Base

class PolicySummaryCache(Base):
    __tablename__ = "policy_summary_cache"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    policy_name = Column(String(200), unique=True, nullable=True)
    summary_text = Column(Text, nullable=True)
    created_at  = Column(DateTime, server_default=func.now())
    updated_at  = Column(DateTime, server_default=func.now(), onupdate=func.now())