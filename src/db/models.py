import uuid
from sqlalchemy import Column, String, Integer, ForeignKey, Text, Float, DateTime, func
from sqlalchemy.dialects.postgresql import UUID
from pgvector.sqlalchemy import Vector
from src.db.config import Base

# 1. Project Model (Must exist for ForeignKey to work)
class Project(Base):
    __tablename__ = "projects"
    id = Column(String, primary_key=True)  # e.g. "order-management"
    name = Column(String)
    created_at = Column(DateTime, default=func.now())

# 2. AnalysisRun Model (MUST HAVE project_id)
class AnalysisRun(Base):
    __tablename__ = "analysis_runs"
    run_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # --- THIS WAS MISSING OR INVALID IN YOUR FILE ---
    project_id = Column(String, ForeignKey("projects.id")) 
    # ------------------------------------------------
    
    status = Column(String, default="IN_PROGRESS")
    created_at = Column(DateTime, default=func.now())

# 3. Business Rule Model
class BusinessRule(Base):
    __tablename__ = "business_rules"
    rule_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id = Column(UUID(as_uuid=True), ForeignKey("analysis_runs.run_id"))
    file_path = Column(String, index=True)
    title = Column(String)
    description = Column(Text)
    code_snippet = Column(Text)
    embedding = Column(Vector(768)) 

# 4. Graph Edge Model
class FileDependency(Base):
    __tablename__ = "file_dependencies"
    source_file = Column(String, primary_key=True) 
    target_file = Column(String, primary_key=True)
    relation_type = Column(String) 

# 5. Graph Node Model (Summary)
class CodeSummary(Base):
    __tablename__ = "code_summaries"
    file_path = Column(String, primary_key=True)
    summary = Column(Text) 
    embedding = Column(Vector(768))