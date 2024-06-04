from motor import motor_asyncio
import hashlib
import os
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
        user_document = {
            'username': username,
            'password': self.hash_password(password)
        }
        return await self.collection.insert_one(user_document)

    async def authencation(self, username, password):
        user = await self.collection.find_one({'username': username})
        salt = user['password'][0:16]
        return user['password'] == self.hash_password(password, salt)

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
        print(channels)

        user = UserCollection()
        await user.add_user('Matheus', '12345678')
        users = await user.get_users()
        print(users)

        print(await user.authencation('Matheus', '12345678'))

    asyncio.run(main())
