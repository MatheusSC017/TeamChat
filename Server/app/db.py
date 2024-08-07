from motor import motor_asyncio
import inspect

from validations import hash_password, validate_password, validate_email, validate_nickname
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

    async def register_channel(self, channel, owner):
        channel_data = await self.get_channel(channel)
        if channel_data is not None:
            return False, ["This channel name is already in use", ]

        channel_document = {
            'Channel': channel,
            'SubChannels': {},
            'owner': owner
        }
        return True, await self.collection.insert_one(channel_document)

    async def update_channel(self, old_channel_name, new_channel_name, owner):
        channel_data = await self.get_channel(new_channel_name)
        if channel_data is not None:
            return False, ["This channel name is already in use", ]

        channel_filter = {
            'Channel': old_channel_name,
            'owner': owner
        }
        response = await self.collection.update_one(channel_filter, {'$set': {'Channel': new_channel_name}})
        if response:
            return True
        return False

    async def delete_channel(self, channel, owner):
        channel_filter = {'Channel': channel, 'owner': owner}
        result = await self.collection.delete_one(channel_filter)
        if result:
            return True
        return False

    async def register_sub_channel(self, channel, sub_channel, owner):
        channel_data = await self.get_channel(channel, owner)
        errors = []
        if channel_data['SubChannels'] is not None and sub_channel in channel_data['SubChannels'].keys():
            errors.append(f'The name "{sub_channel}" is already in use on this channel')

        if len(errors) == 0:
            channel_filter = {'Channel': channel, 'owner': owner}
            channel_data['SubChannels'][sub_channel] = {}
            await self.collection.update_one(channel_filter, {'$set': {'SubChannels': channel_data['SubChannels']}})
            return True, []
        else:
            return False, errors

    async def update_sub_channels(self, channel, sub_channels, owner):
        channel_filter = {'Channel': channel, 'owner': owner}

        errors = []
        for sub_channel in sub_channels:
            if sub_channels[sub_channel].get('enable_password', False):
                if validate_password(sub_channels[sub_channel].get('password', '')):
                    sub_channels[sub_channel]['password'] = hash_password(sub_channels[sub_channel]['password'])
                else:
                    errors.append("Invalid password")
            if sub_channels[sub_channel].get('limit_users', False):
                if sub_channels[sub_channel].get('number_of_users', 0) < 2:
                    errors.append("The number of users must be greater than or equal to 2")

        if len(errors) == 0:
            result = await self.collection.update_one(channel_filter, {'$set': {'SubChannels': sub_channels}})
            if result:
                return True, result
            return False, result
        return False, errors

    async def delete_sub_channels(self, channel, sub_channels, owner):
        channel_data = await self.get_channel(channel, owner)
        if channel_data is None:
            return False
        actual_sub_channels = channel_data.get('SubChannels', {})

        for sub_channel in sub_channels:
            if sub_channel in actual_sub_channels.keys():
                del actual_sub_channels[sub_channel]

        channel_filter = {'Channel': channel, 'owner': owner}
        result = await self.collection.update_one(channel_filter, {'$set': {'SubChannels': actual_sub_channels}})
        if result:
            return True
        return False

    async def get_channels(self, owner=None):
        if owner:
            channels = await self.collection.find({'owner': owner}).to_list(length=None)
        else:
            channels = await self.collection.find().to_list(length=None)

        channels = {channel['Channel']: {field: value for field, value in channel.get('SubChannels', {}).items()}
                    for channel in channels}

        return channels

    async def get_channel(self, channel, owner=None):
        channel_filter = {'Channel': channel, }
        if owner is not None:
            channel_filter['owner'] = owner
        return await self.collection.find_one(channel_filter)


class UserCollection(MongoDB):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._collection_name = 'Users'

    async def add_user(self, **kwargs):
        required_fields = ('username', 'password')
        user_document = {key: value for key, value in kwargs.items() if key in ('username', 'password', 'nickname', 'email')}
        errors = (self.check_required_fields(user_document, required_fields))
        errors.extend(await self.validate_fields(required_fields=required_fields, **user_document))

        if len(errors) == 0:
            user_document['password'] = hash_password(user_document['password'])
            return True, await self.collection.insert_one(user_document)
        return False, errors

    async def update_user(self, username, new_values):
        user_data = await self.get_user(username)
        errors = await self.validate_fields(user=user_data, **new_values)

        if len(errors) == 0:
            user_filter = {
                'username': username,
            }
            return True, await self.collection.update_one(user_filter, {'$set': new_values})
        return False, errors

    async def update_password(self, username, password):
        user_data = await self.get_user(username)
        errors = await self.validate_fields(user=user_data, password=password)

        if len(errors) == 0:
            user_filter = {
                'username': username,
            }
            return True, await self.collection.update_one(user_filter, {'$set': {'password': hash_password(password)}})
        return False, errors

    async def authenticate(self, username, password):
        user = await self.get_user(username)
        if not user:
            return False
        salt = user['password'][0:16]
        return user['password'] == hash_password(password, salt)

    async def get_user(self, username):
        return await self.collection.find_one({'username': username})

    async def get_users(self):
        users = await self.collection.find().to_list(length=None)
        return users

    def check_required_fields(self, fields, required_fields):
        errors = []
        for field in required_fields:
            if (field not in fields.keys() or
                    fields[field] is None or
                    (type(fields[field]) is str and len(fields[field].strip()) == 0)):
                errors.append(f'The field {field} is required')

        return errors

    async def validate_fields(self, user=None, required_fields=[], **kwargs):
        validations = {
            'username': [(self.validate_username_in_user, "Username already in use"),
                         (self.validate_username_length, "Username must contain 4 characters or more")],
            'password': [(validate_password, "The password must contain 8 characters or more, consisting of at least one"
                                             " uppercase letter, one lowercase letter, a number and a special character"), ],
            'email': [(validate_email, "Enter a valid email in the format email@provider.com"), ],
            'nickname': [(validate_nickname, "The nickname must contain at least 4 characters"), ],
        }
        errors = []
        for field, value in kwargs.items():
            if field not in validations.keys():
                errors.append(f"{field} is not a valid field")
                continue

            if field not in required_fields and (value is None or (type(value) is str and len(value) == 0)):
                continue

            for validation, error_message in validations[field]:
                if inspect.iscoroutinefunction(validation):
                    valid_field = await validation(value, user_data=user or {})
                else:
                    valid_field = validation(value, user_data=user or {})

                if not valid_field:
                    errors.append(error_message)

        return errors

    async def validate_username_in_user(self, username, user_data={}):
        users = await self.get_users()
        users = [user['username'] for user in users]
        return user_data.get('username') == username or username not in users

    def validate_username_length(self, username, **kwargs):
        return len(username) >= 4


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
