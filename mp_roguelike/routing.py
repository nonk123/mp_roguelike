from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter

from django.urls import re_path

from . import consumers

urlpatterns = [
    re_path("server/", consumers.RoguelikeConsumer)
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(URLRouter(urlpatterns))
})
