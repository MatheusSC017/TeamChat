import secrets
import redis


class UserToken:
    def __init__(self):
        self.redis_conn = redis.Redis()

    def add_user(self, username):
        token = secrets.token_bytes(64)
        self.redis_conn.set(token, username)
        return token

    def del_user(self, token):
        _, user_exist = self.authenticate(token)
        if user_exist:
            self.redis_conn.delete(token)
            return True
        return False

    def authenticate(self, token):
        username = self.redis_conn.get(token)
        if username is None:
            return '', False
        return username, True
