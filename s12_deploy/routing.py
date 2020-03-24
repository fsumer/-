from channels.routing import ProtocolTypeRouter,URLRouter
from django.conf.urls import url
from app01 import consumers



"""consumers.py 当逻辑也非常多的时候 你也可以建成文件夹里面包含多个文件的形式"""
application = ProtocolTypeRouter({
    'websocket':URLRouter([
        url(r'^publish/(?P<task_id>\d+)/$',consumers.PublishConsumer)
    ])
})