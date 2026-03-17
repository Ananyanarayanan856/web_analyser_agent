from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Float
from datetime import datetime
from app.database import Base

class Website(Base):
    __tablename__ = "websites"

    website_id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_scanned = Column(DateTime, nullable=True)
    seo_status = Column(String, nullable=True)
    accessibility_status = Column(String, nullable=True)
    content_status = Column(String, nullable=True)

class SeoReport(Base):
    __tablename__ = "seo_reports"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    grade = Column(String, nullable=True)
    issues = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AccessibilityReport(Base):
    __tablename__ = "accessibility_reports"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    grade = Column(String, nullable=True)
    issues = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class ContentReport(Base):
    __tablename__ = "content_reports"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    score = Column(Float, nullable=True)
    grade = Column(String, nullable=True)
    word_count = Column(Integer, nullable=True)
    readability = Column(String, nullable=True)
    issues = Column(Text, nullable=True)
    details = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class AnalysisSummary(Base):
    __tablename__ = "analysis_summary"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, nullable=False)
    summary = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class DbLog(Base):
    __tablename__ = "db_logs"

    log_id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    operation = Column(String, nullable=True)
    table_name = Column(String, nullable=True)
    query = Column(Text, nullable=True)
    status = Column(String, nullable=True)
    error_message = Column(Text, nullable=True)
    executed_by = Column(String, nullable=True)

