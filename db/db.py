import os

from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv()
engine = create_async_engine(os.environ['DATABASE_URL'], echo=True)
Session = async_sessionmaker(engine, expire_on_commit=False)


class Base(DeclarativeBase):
    """Declarative base class creation"""
    pass


async def get_db() -> AsyncSession:
    """ Returns the asynchronous session generator """
    async with Session() as session:
        yield session
