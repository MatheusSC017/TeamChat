# TeamChat

This project consists of a chat application which is divided into two parts, the first is the server which is responsible for maintaining the chat structure (channels and subchannels) and establishing a communication point for connected users, the second part is the client, which is developed in Python, together with the PyQT library to create an interface in which the user can interact with the server structure and communicate with other users

## Users

Creating a user is very simple. You only need to set a username and a password. Optionally, you can also set an email and a nickname for auto-connecting in the chat.

## Chats

Chats have an owner and sub-channels. The owner is the user who creates and manages the channel. The sub-channels are the rooms where users can enter to chat.

Each sub-channel has several configurations:

Password: This configuration consists of two values:
    A boolean indicating if the sub-channel is private or public.
    If the sub-channel is private, the owner needs to specify a password.

User Limit: This configuration limits the number of users that can be connected to a specific sub-channel. You can set whether the sub-channel has a user limit, and if so, what that limit is.

Anonymous Users: This boolean setting indicates if the sub-channel accepts anonymous users or only logged-in users.