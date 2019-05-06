from twisted.application import internet, service
from chat.chat_server import config
from chat.chat_server.server import ChatServer
from chat.chat_server.db import DBService

chat_service = service.MultiService()

db_service = DBService()
db_service.setServiceParent(chat_service)

comm_server = ChatServer(db_service)
comm_service = internet.TCPServer(config.server_port, comm_server, interface=config.server_host)
comm_service.setServiceParent(chat_service)

application = service.Application('chat_service')
chat_service.setServiceParent(application)
