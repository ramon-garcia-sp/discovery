from dataclasses import dataclass

from sqlalchemy import (TIMESTAMP, Boolean, Column, Integer, String, Text,
                        create_engine, func)
from sqlalchemy.orm import declarative_base, sessionmaker

Base = declarative_base()


@dataclass
class Service(Base):
    __tablename__ = "services"

    id: int = Column(Integer, primary_key=True, autoincrement=True)
    service_name: str = Column(String(255), nullable=False)
    owner_team: str = Column(String(255), nullable=False)
    repository_source: str = Column(Text, nullable=False)
    lifecycle_status: str = Column(String(50), nullable=False)
    consolidation_conflict: bool = Column(Boolean, default=False)
    last_updated: str = Column(
        TIMESTAMP, nullable=False, server_default=func.now(), onupdate=func.now()
    )


# Define a function to initialize the database engine and session
def init_db(config):
    engine = create_engine(config.SQLALCHEMY_DATABASE_URI)
    Session = sessionmaker(bind=engine)
    return engine, Session
