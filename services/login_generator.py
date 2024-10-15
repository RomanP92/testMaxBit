import secrets
import string

from transliterate import translit

from const import RANDOM_LENGTH
from db.models import User
from services.services import retranslation


def transliterate_name(name: str) -> str:
    """Cyrillic transliteration of the first Cyrillic word of the name to create a username"""
    word = name.split()[0]
    login_word = translit(word, 'ru', reversed=True)
    return login_word


def generate_random_string(name: str, random_length: int) -> str:
    """Creating a random login"""
    trans_name = transliterate_name(name)
    symbols_collection = string.ascii_letters + string.digits
    rand_login = trans_name + '_' + ''.join(secrets.choice(
        symbols_collection) for i in range(random_length))
    return rand_login


async def get_random_login(name: str) -> list:
    """creating a list of random logins with uniqueness check"""
    login = transliterate_name(name)
    db_logins = await retranslation(User.get_logins_for_cheking, login=login)
    new_logins = []
    while len(new_logins) < 3:
        login = generate_random_string(name, RANDOM_LENGTH)
        if login not in db_logins:
            new_logins.append(login)
    return new_logins
