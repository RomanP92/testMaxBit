import contextlib
import logging
import os
from typing import AsyncIterator

from dotenv import load_dotenv

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase

load_dotenv()
log_db = logging.getLogger(__name__)
log_db.setLevel(logging.INFO)
log_handler = logging.FileHandler(f"{__name__}.log", mode='w')
log_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
log_handler.setFormatter(log_formatter)
log_db.addHandler(log_handler)


class DatabaseSessionManager:
    """Sessions manager"""

    def __init__(self, db_url: str, echo: bool = False) -> None:
        self.engine = create_async_engine(db_url, echo=echo)
        self._session_maker = async_sessionmaker(self.engine, expire_on_commit=False)

    @contextlib.asynccontextmanager
    async def session_gen(self) -> AsyncIterator[AsyncSession]:
        if self._session_maker is None:
            raise Exception("DatabaseSessionManager is not initialized")
        session = self._session_maker()
        try:
            yield session
        except Exception as e:
            log_db.exception(e, exc_info=True)
            await session.rollback()
        finally:
            await session.close()


sessionmanager = DatabaseSessionManager(db_url=os.environ['DATABASE_URL'])


class Base(DeclarativeBase):
    """Declarative base class creation"""
    pass


async def get_db() -> AsyncSession:
    """ Returns the asynchronous session generator """
    async with sessionmanager.session_gen() as session:
        yield session
