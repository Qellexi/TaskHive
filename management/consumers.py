import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async

from management.models import ChatRoom, Message


class PrivateChatConsumer(AsyncWebsocketConsumer):

    @database_sync_to_async
    def get_or_create_room(self, uid1, uid2):
        name = f"private_{uid1}_{uid2}"
        room, created = ChatRoom.objects.get_or_create(name=name)
        return room

    @database_sync_to_async
    def add_members(self, room, w1, w2):
        room.members.add(w1, w2)

    @database_sync_to_async
    def load_history(self, room):
        messages = room.chats.order_by("timestamp")
        return [
            {
                "sender": m.sender.username,
                "sender_id": m.sender.id,
                "content": m.content,
                "timestamp": m.timestamp.isoformat()
            }
            for m in messages
        ]

    @database_sync_to_async
    def save_message(self, sender, content, room):
        Message.objects.create(sender=sender, content=content, room=room)

    async def connect(self):
        self.worker1 = self.scope['user']
        self.worker1_id = int(self.scope['url_route']['kwargs']['worker1_id'])
        self.worker2_id = int(self.scope['url_route']['kwargs']['worker2_id'])

        uid1, uid2 = sorted([self.worker1_id, self.worker2_id])
        self.room_group_name = f"private_{uid1}_{uid2}"

        # FIXED: ORM must be awaited with database_sync_to_async
        self.room = await self.get_or_create_room(uid1, uid2)
        await self.add_members(self.room, self.worker1_id, self.worker2_id)

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        # FIXED: async ORM wrapper
        history = await self.load_history(self.room)

        await self.send(text_data=json.dumps({
            "type": "history",
            "messages": history
        }))

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message = data["message"]
        sender = self.scope["user"]

        # FIXED: async save
        await self.save_message(sender, message, self.room)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": sender.username,
                "sender_id": sender.id,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "sender_id": event["sender_id"],
        }))



class GroupChatConsumer(AsyncWebsocketConsumer):
    @database_sync_to_async
    def get_room(self, room_id):
        return ChatRoom.objects.get(id=room_id)

    @database_sync_to_async
    def load_history(self, room):
        return [
            {
                "sender": m.sender.username,
                "sender_id": m.sender.id,
                "content": m.content,
                "timestamp": m.timestamp.isoformat()
            }
            for m in room.chats.order_by("timestamp")
        ]

    @database_sync_to_async
    def save_message(self, sender, content, room):
        Message.objects.create(sender=sender, content=content, room=room)

    async def connect(self):
        self.room_id = int(self.scope["url_route"]["kwargs"]["room_id"])
        self.room = await self.get_room(self.room_id)

        self.room_group_name = f"group_{self.room_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        history = await self.load_history(self.room)

        await self.send(text_data=json.dumps({
            "type": "history",
            "messages": history
        }))

    async def receive(self, text_data=None, bytes_data=None):
        data = json.loads(text_data)
        message = data["message"]
        sender = self.scope["user"]

        await self.save_message(sender, message, self.room)

        await self.channel_layer.group_send(
            self.room_group_name,
            {
                "type": "chat_message",
                "message": message,
                "sender": sender.username,
                "sender_id": sender.id,
            }
        )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            "message": event["message"],
            "sender": event["sender"],
            "sender_id": event["sender_id"],
        }))
