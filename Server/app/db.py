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
        self.collection.insert_one(user_document)

    async def get_users(self):
        users = await self.collection.find().to_list(length=None)
        return users

    @staticmethod
    def hash_password(password):
        salt = os.urandom(16)
        password_hash = hashlib.sha256(salt + password.encode())
        return salt + password_hash.digest()


if __name__ == '__main__':
    import asyncio
    import time

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
        time.sleep(3)
        users = await user.get_users()
        print(users)

    asyncio.run(main())
