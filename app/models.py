from sqlalchemy import Column, String, Text, DateTime
from datetime import datetime
from app.database import Base


class ProjectFact(Base):
    __tablename__ = "project_facts"

    id = Column(String, primary_key=True)
    project_id = Column(String, index=True)
    project_name = Column(String, index=True)
    fact_type = Column(String, index=True)
    question_key = Column(String, index=True)
    answer = Column(Text)
    updated_at = Column(DateTime, default=datetime.utcnow)