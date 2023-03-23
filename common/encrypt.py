import hashlib
import random
import string


def random_str(length=6, chars=string.ascii_lowercase):
    return ''.join(random.sample(chars, length))


def md5(s, salt='', encoding='utf-8') -> str:
    if isinstance(s, str):
        return hashlib.md5((s + salt).encode(encoding=encoding)).hexdigest()
    else:
        return hashlib.md5(s).hexdigest()






