import twisted.internet.protocol as protocol
from chat import irc
from chat.chat_server import db


class InitialProtocol(irc.IRC):
    # TODO: no. 1: implement receiver methods in irc.IRC, use them here, CONNECT/REGISTER/LOGIN - proceed,
    # otherwise - loseConnection!
    INITIAL = 0
    CLIENT = 1
    CHAT_SERVER = 2
    AI_SERVER = 3

    def __init__(self):
        self.state = self.INITIAL

    def connectionMade(self):
        pass

    def connectionLost(self, reason):
        pass


class Dispatcher(protocol.Factory):
    protocol = InitialProtocol

    def __init__(self):
        # TODO: peer set class?
        self.peers = []


class ChatServer:
    def __init__(self):
        self.dispatcher = Dispatcher()
        self.db = db.Database()
