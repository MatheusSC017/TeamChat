from motor import motor_asyncio
import hashlib
import os

from validations import validate_password
from settings import MONGODB_URI


class MongoDB:
    _client = None
    _db = None
    _collection = None
    _collection_name = None

    def __init__(self):
        self._client = motor_asyncio.AsyncIOMotorClient(MONGODB_URI)

    @property
    def db(self):
        if self._db is None:
            self._db = self._client['TeamChat']

        return self._db

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.db[self._collection_name]

        return self._collection


class ChatCollection(MongoDB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collection_name = 'Chats'

    async def get_channels(self):
        channels = await self.collection.find().to_list(length=None)

        channels = {channel['Channel']: {sub_channel: {} for sub_channel in channel['SubChannels']}
                    for channel in channels}

        return channels


class UserCollection(MongoDB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collection_name = 'Users'

    async def add_user(self, username, password):
        users = await self.get_users()
        users = [user['username'] for user in users]

        errors = []
        if username in users:
            errors.append("Username already in use")

        if not validate_password(password):
            errors.append("The password must contain 8 characters or more, consisting of at least one uppercase letter,"
                          " one lowercase letter, a number and a special character")

        if len(errors) == 0:
            user_document = {
                'username': username,
                'password': self.hash_password(password)
            }
            return True, await self.collection.insert_one(user_document)
        return False, errors

    async def authenticate(self, username, password):
        user = await self.get_user(username)
        salt = user['password'][0:16]
        return user['password'] == self.hash_password(password, salt)

    async def get_user(self, username):
        return await self.collection.find_one({'username': username})

    async def get_users(self):
        users = await self.collection.find().to_list(length=None)
        return users

    @staticmethod
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


if __name__ == '__main__':
    import asyncio

    channels = {
        "Global": {
            'Logs': {}
        }
    }

    async def main():
        chat = ChatCollection()
        channels.update(await chat.get_channels())
        print('Channels')
        print(channels)
        print('*' * 40)

        user = UserCollection()
        print('Register User')
        print(await user.add_user('Matheus', 'P@ssw0rd'))
        print('*' * 40)

        users = await user.get_users()
        print('Users')
        print(users)
        print('*' * 40)

        print('Authenticate')
        print(await user.authenticate('Matheus', 'P@ssw0rd'))
        print('*' * 40)

    asyncio.run(main())
