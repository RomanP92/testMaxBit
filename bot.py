import logging
import os

from pyrogram import Client, filters
from pyrogram_patch import patch
from pyrogram_patch.fsm import State, StatesGroup, StateItem
from pyrogram_patch.fsm.filter import StateFilter
from pyrogram.types import CallbackQuery, Message

from const import RANDOM_ANSWER_TEXT
from db.models import User, Task
from keyboards.keyboards import get_start_keyboard, get_tasks_keyboard, get_task_item_keyboard, get_logins_keyboard, \
    get_back_button_keyboard
from services.login_generator import get_random_login
from services.services import MemoryStorage, retranslation, check_registration, get_button_text

# from pyrogram_patch.fsm.storages import RedisStorage

log = logging.getLogger(__name__)
log.setLevel(logging.INFO)
log_handler = logging.FileHandler(f"{__name__}.log", mode='w')
log_formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
log_handler.setFormatter(log_formatter)
log.addHandler(log_handler)

start_keyboard = get_start_keyboard()
app = Client("my_ac",
             api_id=os.environ['API_ID'],
             api_hash=os.environ['API_HASH'],
             bot_token=os.environ['BOT_TOKEN'])
patch_manager = patch(app)
patch_manager.set_storage(MemoryStorage())
# patch_manager.set_storage(RedisStorage())

messages_id = []


class MyStates(StatesGroup):
    """bot state creation"""
    registration_name = StateItem()
    registration_login = StateItem()
    menu_keyboard = StateItem()
    my_task = StateItem()
    task_description = StateItem()
    created_task = StateItem()
    task_item = StateItem()


@app.on_message(filters.command("start"))
async def start_handler(_: Client, message: Message, state: State):
    """check registration, display a message for entering a name
            or a message indicating that registration is available
            and a start keypad for registered users"""
    await state.finish()
    telegram_user_id = message.from_user.id
    db_user = await retranslation(method=User.get_user_for_telegram_id, telegram_id=telegram_user_id)
    if db_user:
        await message.reply(text='Вы уже зарегистрированы, предлагаем перейти к работе',
                            reply_markup=start_keyboard)
        await state.set_state(MyStates.menu_keyboard)
    else:
        await message.reply('Для регистрации введите свое имя')
        await state.set_data({'telegram_id': telegram_user_id})
        await state.set_state(MyStates.registration_name)


@app.on_message(filters.regex(r'^[a-zA-Zа-яА-ЯёЁ]+$') & StateFilter(MyStates.registration_name))
async def input_name_handler(_: Client, message: Message, state: State):
    """Outputs a name acceptance message and shows buttons for login selection"""
    name = message.text
    logins = await get_random_login(name)
    logins_keyboard = get_logins_keyboard(logins)
    mess = await message.reply(text=f'Отлично, Ваше имя <b>{message.text}</b>\nТеперь выберите Login',
                               reply_markup=logins_keyboard)
    messages_id.append(mess.id)
    await state.set_data({'name': message.text})
    await state.set_state(MyStates.registration_login)


@app.on_callback_query(filters.regex('login') & StateFilter(MyStates.registration_login))
async def input_login_handler(client: Client, callback: CallbackQuery, state: State):
    """shows the login acceptance message and displays the start keyboard"""
    login = get_button_text(callback=callback)
    await state.set_data({'login': login})
    data = await state.get_data()
    await retranslation(method=User.create_user, **data)
    await callback.message.edit_text(text=f'Отлично, Ваш Login: <b>{login}</b>\nПредлагаем приступить к работе')
    await callback.message.reply(text='Воспользуйтесь клавиатурой', reply_markup=start_keyboard)
    await state.set_state(MyStates.menu_keyboard)
    await client.answer_callback_query(callback_query_id=callback.id)


@app.on_callback_query(filters.regex('my_tasks'))
@app.on_message(filters.regex('Мои Задачи'))
@check_registration
async def watch_my_task_handler(client: Client, trigger: Message|CallbackQuery, state: State, **kwargs):
    """show task list"""
    db_user = kwargs.get('db_user')
    await state.set_data({'id': db_user.id})
    task_list = await retranslation(Task.get_all_my_tasks, user_id=db_user.id)
    if task_list:
        text = 'Сохраненные задачи:'
        keyboard = get_tasks_keyboard(task_list)
    else:
        text = 'У Вас нет задач'
        keyboard = start_keyboard
    if isinstance(trigger, Message):
        await client.delete_messages(chat_id=trigger.chat.id, message_ids=messages_id)
        messages_id.clear()
        mess = await trigger.reply(text=text, reply_markup=keyboard)
    elif isinstance(trigger, CallbackQuery):
        mess = await trigger.message.edit_text(text=text, reply_markup=keyboard)
        await client.answer_callback_query(callback_query_id=trigger.id)
    messages_id.append(mess.id)
    await state.set_state(MyStates.my_task)


@app.on_message(filters.regex('Создать Задачу'))
@check_registration
async def create_name_task_handler(client: Client, message: Message, state: State, **kwargs):
    """processing of pressing the button of task creation with registration verification"""
    if messages_id:
        await client.delete_messages(chat_id=message.chat.id, message_ids=messages_id)
        messages_id.clear()
    await message.reply(text='Укажите название задачи:')
    await state.set_state(MyStates.task_description)


@app.on_message(StateFilter(MyStates.task_description))
async def create_description_task_handler(_: Client, message: Message, state: State):
    """output a message about accepting the title and output a sentence about entering a task description"""
    await message.reply(text='Укажите описание задачи:')
    await state.set_data({'name': message.text})
    await state.set_state(MyStates.created_task)


@app.on_message(StateFilter(MyStates.created_task))
async def save_task_handler(_: Client, message: Message, state: State):
    """task preservation"""
    telegram_user_id = message.from_user.id
    await state.set_data({'description': message.text})
    data = await state.get_data()
    name = data.get('name')
    description = data.get('description')
    db_user = await retranslation(method=User.get_user_for_telegram_id, telegram_id=telegram_user_id)
    if name and description:
        try:
            await retranslation(Task.create_task, name=name, description=description, user_id=db_user.id)
        except:
            await message.reply(text='Произошла ошибка, начните заново', reply_markup=start_keyboard)
        else:
            await message.reply(text='Задача успешно сохранена', reply_markup=start_keyboard)
        finally:
            await state.finish()

    else:
        await message.reply(text='Произошла ошибка')
        await state.finish()


@app.on_callback_query(filters.regex(r"^task_\d+$") & StateFilter(MyStates.my_task))
async def watch_task_item_handler(client: Client, callback: CallbackQuery, state: State):
    task_id = callback.data.lstrip('task_')
    task = await retranslation(method=Task.get_one, id=task_id)
    completed_text = '✔️ Отменить выполнение' if task.completed else '❌ Не выполнено'
    task_name = get_button_text(callback)
    mess = await callback.message.edit_text(
        text=f'Задача <b>{task_name.lstrip('✔️').lstrip('❌')}</b>:\n\n {task.description}',
        reply_markup=get_task_item_keyboard(completed_text))
    messages_id.append(mess.id)
    await client.answer_callback_query(callback_query_id=callback.id)
    await state.set_state(StateFilter(MyStates.task_item))
    await state.set_data({'task_id': task_id})


@app.on_callback_query(filters.regex('completed'))
async def mark_completed(client: Client, callback: CallbackQuery, state: State):
    data = await state.get_data()
    keyboard = callback.message.reply_markup.inline_keyboard
    button_name = keyboard[0][1].text
    if button_name.startswith('✔️'):
        await retranslation(Task.update_complete, id=data.get('task_id'), completed=False)
        mess = await callback.message.edit_reply_markup(reply_markup=get_task_item_keyboard('❌ Не выполнено'))
    elif button_name.startswith('❌'):
        await retranslation(Task.update_complete, id=data.get('task_id'), completed=True)
        mess = await callback.message.edit_reply_markup(
            reply_markup=get_task_item_keyboard('✔️ Отменить выполнение'))
    messages_id.append(mess.id)
    await client.answer_callback_query(callback_query_id=callback.id)


@app.on_callback_query(filters.regex('delete_task'))
async def delete_task(client: Client, callback: CallbackQuery, state: State):
    data = await state.get_data()
    task_id = data.get('task_id')
    await retranslation(Task.delete_task, id=task_id)
    await callback.answer(text=f'Задача удалена', show_alert=False)
    mess = await callback.message.edit_text(text='Нажмите <b>Назад</b> для возврата к задачам',
                                            reply_markup=get_back_button_keyboard())
    messages_id.append(mess.id)
    await client.answer_callback_query(callback_query_id=callback.id)


@app.on_message()
async def random_message_answer(client: Client, message: Message):
    await client.delete_messages(chat_id=message.chat.id, message_ids=messages_id)
    messages_id.clear()
    await message.reply(text=RANDOM_ANSWER_TEXT, reply_markup=start_keyboard)


app.run()
