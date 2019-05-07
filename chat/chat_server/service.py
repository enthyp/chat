from twisted.application import service
from chat.chat_server.server import ChatServer
from chat.chat_server.db import DBService

chat_service = service.MultiService()

db_service = DBService()
db_service.setServiceParent(chat_service)

comm_service = ChatServer(db_service)
comm_service.setServiceParent(chat_service)

application = service.Application('chat_service')
chat_service.setServiceParent(application)
