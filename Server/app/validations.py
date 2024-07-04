import re
import hashlib
import os

password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*().]).{8,}"
email_regex = r"^([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+"


def validate_password(password, **kwargs):
    if re.search(password_regex, password):
        return True
    return False


def validate_email(email, **kwargs):
    if re.search(email_regex, email):
        return True
    return False


def validate_nickname(nickname, **kwargs):
    if len(nickname) > 3:
        return True
    return False


def hash_password(password, salt=None):
    if salt is None:
        salt = os.urandom(16)
    interations = int(1e5)
    password_hash = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt,
        interations
    )
    return salt + password_hash
