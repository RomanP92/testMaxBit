from typing import Callable

from pyrogram import Client
from pyrogram.types import Message
from pyrogram_patch.fsm import State

from db.db import sessionmanager
from db.models import User
from services.services import log_serv


async def create_name_task_handler(_: Client, message: Message, __: State):
    """displaying a message about the need to register"""
    await message.reply(text='Вы не зарегистрированы. Для регистрации нажмите <b>/start</b>')


def check_registration(func: Callable) -> Callable:
    """user registration verification decorator"""

    async def wrapper(*args, **kwargs):
        try:
            client, message = args
            state = kwargs.get('state')
        except ValueError as e:
            log_serv.exception(e, exc_info=True)
            return e
        telegram_id = message.from_user.id
        async with sessionmanager.session_gen() as session:
            db_user = await User.get_user_for_telegram_id(db=session, telegram_id=telegram_id)
            if db_user is not None:
                return await func(client, message, state, db_user=db_user)
            else:
                return await create_name_task_handler(client, message, state)

    return wrapper
