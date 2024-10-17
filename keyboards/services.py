from pyrogram.types import CallbackQuery


def get_button_text(callback: CallbackQuery) -> str:
    """inline key text retrieval"""
    keyboard = callback.message.reply_markup.inline_keyboard
    for row in keyboard:
        for button in row:
            if button.callback_data == callback.data:
                return button.text
