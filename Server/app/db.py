from motor import motor_asyncio
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
        return await self.collection.find().to_list(length=None)


if __name__ == '__main__':
    import asyncio

    async def main():
        chat = ChatCollection()
        channels = await chat.get_channels()

        print(channels)

    asyncio.run(main())
