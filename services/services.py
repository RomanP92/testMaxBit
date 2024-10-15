from typing import Callable, Any

from pyrogram import Client
from pyrogram_patch.fsm import State
from pyrogram_patch.fsm.storages import MemoryStorage as Ms
from pyrogram.types import CallbackQuery, Message

from db.db import get_db
from db.models import User, Task


class MemoryStorage(Ms):
    """change class method for reset state and date"""
    async def finish_state(self, key: str) -> None:
        if key in self.__storage.keys():
            self.__storage.clear()
        if key in self.__data_storage:
            self.__data_storage.clear()


async def retranslation(method: Callable, **kwargs) -> Any:
    """obtaining a session and executing a method to work with the database"""
    session_gen = get_db()
    session_ = anext(session_gen)
    session = await session_
    result = await method(db=session, **kwargs)
    return result


async def create_name_task_handler(client: Client, message: Message, state: State):
    """displaying a message about the need to register"""
    await message.reply(text='Вы не зарегистрированы. Для регистрации нажмите <b>/start</b>')


def check_registration(func: Callable) -> Callable:
    """user registration verification decorator"""
    async def wrapper(*args, **kwargs):
        try:
            client, message = args
            state = kwargs.get('state')
        except ValueError as e:
            return e
        telegram_id = message.from_user.id
        session_gen = get_db()
        session_ = anext(session_gen)
        async with await session_ as session:
            db_user = await User.get_user_for_telegram_id(db=session, telegram_id=telegram_id)
            if db_user is not None:
                return await func(client, message, state, db_user=db_user)
            else:
                return await create_name_task_handler(client, message, state)
    return wrapper


def get_button_text(callback: CallbackQuery) -> str:
    """inline key text retrieval"""
    keyboard = callback.message.reply_markup.inline_keyboard
    for row in keyboard:
        for button in row:
            if button.callback_data == callback.data:
                return button.text
