import logging
from typing import Callable, Any

from pyrogram_patch.fsm.storages import MemoryStorage as Ms
from sqlalchemy.exc import SQLAlchemyError

from db.db import sessionmanager

log_serv = logging.getLogger(__name__)
log_serv.setLevel(logging.INFO)
log_handler = logging.FileHandler(f"{__name__}.log", mode='w')
log_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
log_handler.setFormatter(log_formatter)
log_serv.addHandler(log_handler)


class MemoryStorage(Ms):
    """change class method for reset state and date"""

    async def finish_state(self, key: str) -> None:
        if key in self.__storage.keys():
            self.__storage.clear()
        if key in self.__data_storage:
            self.__data_storage.clear()


async def retranslation(method: Callable, **kwargs) -> Any:
    """obtaining a session and executing a method to work with the database"""
    async with sessionmanager.session_gen() as session:
        try:
            result = await method(db=session, **kwargs)
        except SQLAlchemyError as e:
            log_serv.exception(e, exc_info=True)
            await session.rollback()
        else:
            return result


