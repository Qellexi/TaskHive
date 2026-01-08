from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    # private chat: ws://host/ws/private/5/10
    re_path(r"ws/private/(?P<worker1_id>\d+)/(?P<worker2_id>\d+)/$",
            consumers.PrivateChatConsumer.as_asgi()),
    #group chat: ws://host/ws/group/<room_name>/
    re_path(r'ws/group/(?P<room_id>\d+)/$',
            consumers.GroupChatConsumer.as_asgi()),
]
