from pyrogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def get_start_keyboard() -> ReplyKeyboardMarkup:
    """returns the start keyboard"""
    start_keyboard = ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='Создать Задачу'),
         KeyboardButton(text='Мои Задачи')]
    ],
        resize_keyboard=True, one_time_keyboard=True, placeholder='Сделайте выбор')
    return start_keyboard


def get_tasks_keyboard(tasks: list) -> InlineKeyboardMarkup:
    """returns a keyboard with a list of tasks"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'{'✔️' if task.completed else '❌'} {task.name}',
                              callback_data=f'task_{task.id}')] for task in tasks])
    return keyboard


def get_task_item_keyboard(completed_text: str) -> InlineKeyboardMarkup:
    """returns the inline keyboard for one task"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='my_tasks'),
         InlineKeyboardButton(text=completed_text, callback_data='completed'),
         InlineKeyboardButton(text='Удалить', callback_data='delete_task')],
    ])
    return keyboard


def get_logins_keyboard(logins: list) -> InlineKeyboardMarkup:
    """returns a keyboard with three login options"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=login, callback_data='login') for login in logins]
    ])
    return keyboard


def get_back_button_keyboard() -> InlineKeyboardMarkup:
    """returns the keyboard with a back button to the task list"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='Назад', callback_data='my_tasks'),
         ],
    ])
    return keyboard
