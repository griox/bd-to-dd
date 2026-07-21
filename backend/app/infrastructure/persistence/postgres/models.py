from datetime import datetime

from sqlalchemy import Column, DateTime, String, Text

from app.infrastructure.persistence.postgres.database import Base


class ProjectModel(Base):
    __tablename__ = "projects"

    id = Column(String, primary_key=True, index=True)
    name = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)


class GenerationJobModel(Base):
    __tablename__ = "generations"

    id = Column(String, primary_key=True, index=True)
    project_id = Column(String, index=True, nullable=False)
    status = Column(String, nullable=False)
    result = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
