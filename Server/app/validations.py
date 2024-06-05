import re

password_regex = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*[0-9])(?=.*[!@#$%^&*().]).{8,}"


def validate_password(password):
    if re.search(password_regex, password):
        return True
    return False
