from PyQt6.QtWidgets import QWidget
from datetime import datetime


class ChatHandler(QWidget, object):
    async def send_input_message(self, message: str, recipient: str = None) -> None:
        if recipient is None:
            await self.websocket.send_json({'action': 'chat_message',
                                            'message': message,
                                            'datetime': datetime.now().strftime('%d/%m/%Y %H:%M:%S')})
        else:
            await self.websocket.send_json({'action': 'direct_message',
                                            'recipient': recipient,
                                            'message': message,
                                            'datetime': datetime.now().strftime('%d/%m/%Y %H:%M:%S')})

    def chat_message_action(self, message_json):
        self.messageReceived.emit(f'{message_json["datetime"]} - '
                                  f'{message_json["user"]}: {message_json["message"]}',
                                  'Local')

    def direct_message_action(self, message_json):
        self.messageReceived.emit(f'{message_json["datetime"]} - '
                                  f'{message_json["user"]}: {message_json["message"]}',
                                  message_json["user"])
