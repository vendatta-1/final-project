# import os
# from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker 
# from sqlalchemy.ext.declarative import declarative_base
# # from sqlalchemy.orm import sessionmaker
# from contextlib import contextmanager


# DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://finalproj:finalproj@localhost:5432/finaldb")

# engine = create_engine(DATABASE_URL, echo=True)


# SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base = declarative_base()

# @contextmanager
# def get_db():
#     db_session = SessionLocal()
#     try:
#         yield db_session
#     finally:
#         db_session.close()


# def create_db_tables():
#     Base.metadata.create_all(bind=engine)




######## update from sync to async

import os
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from sqlalchemy.orm import declarative_base
from contextlib import asynccontextmanager
from sqlalchemy import create_engine
# Use asyncpg or psycopg async driver
DATABASE_URL = os.getenv(
    "DATABASE_URL", 
    "postgresql+asyncpg://postgres:tPZbWbzZLswoNhxDVqRtuODeeClrCkmm@yamabiko.proxy.rlwy.net:32737/railway"
)


# Create async engine
engine = create_async_engine(DATABASE_URL, echo=True)

# Async session factory
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()

# Async dependency for FastAPI
async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
