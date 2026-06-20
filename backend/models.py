# backend/models.py
import os
from datetime import datetime, timezone
from sqlalchemy import (
    create_engine, Column, String, Integer, 
    Text, DateTime, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from dotenv import load_dotenv

load_dotenv()

Base = declarative_base()
engine = create_engine(os.getenv("DATABASE_URL"))
SessionLocal = sessionmaker(bind=engine)


# --- Table 1: every PR that was reviewed ---
class PullRequest(Base):
    __tablename__ = "pull_requests"

    id         = Column(Integer, primary_key=True, autoincrement=True)
    repo_name  = Column(String, nullable=False)
    pr_number  = Column(Integer, nullable=False)
    pr_title   = Column(String, nullable=False)
    reviewed_at = Column(DateTime, default=lambda: datetime.now(timezone.utc))

    findings   = relationship("Finding", back_populates="pull_request")


# --- Table 2: individual issues found per PR ---
class Finding(Base):
    __tablename__ = "findings"

    id          = Column(Integer, primary_key=True, autoincrement=True)
    pr_id       = Column(Integer, ForeignKey("pull_requests.id"), nullable=False)
    file_path   = Column(String)
    line_number = Column(String)
    severity    = Column(String)
    issue       = Column(Text)
    suggestion  = Column(Text)

    pull_request = relationship("PullRequest", back_populates="findings")


def create_tables():
    Base.metadata.create_all(engine)