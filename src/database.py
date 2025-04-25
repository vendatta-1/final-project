import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager


DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://finalproj:finalproj@localhost:5432/finaldb")

engine = create_engine(DATABASE_URL, echo=True)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

@contextmanager
def get_db():
    db_session = SessionLocal()
    try:
        yield db_session
    finally:
        db_session.close()


def create_db_tables():
    Base.metadata.create_all(bind=engine)
