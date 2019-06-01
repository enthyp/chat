from twisted.python import log, failure
from twisted.internet import protocol, defer
from twisted.application import service
from twisted.internet.endpoints import TCP4ClientEndpoint, connectProtocol

from chat import config
from chat.chat_server import peer
from chat.chat_server import dispatch
from chat import communication as comm


class PeerFactory(protocol.Factory):

    protocol = comm.BaseProtocol

    class InitialSubscriber(comm.MessageSubscriber):
        def __init__(self, factory, protocol):
            self.protocol = protocol
            self.factory = factory

        def handle_message(self, message):
            if message.command in ('REGISTER', 'LOGIN'):
                self.factory.chat_client_connected(self.protocol, message)
            elif message.command == 'CONNECT':
                self.factory.chat_server_connected(self.protocol, message)
            else:
                self.factory.bad_message(self.protocol, message)

        def on_connection_closed(self):
            log.msg('Connection lost before server/client differentiation.')

    def __init__(self, db, dispatcher, ai_conn):
        self.db = db
        self.dispatcher = dispatcher
        self.ai_conn = ai_conn

    def buildProtocol(self, addr):
        protocol = self.protocol()
        subscriber = self.InitialSubscriber(self, protocol)
        protocol.register_subscriber(subscriber)

        return protocol

    def chat_client_connected(self, protocol, message):
        endpoint = peer.ChatClientEndpoint(protocol)
        client_peer = peer.ChatClient(self.db, self.dispatcher, self.ai_conn, protocol, endpoint)
        client_peer.state_init(message)

    def chat_server_connected(self, protocol, message):
        endpoint = peer.ChatServerEndpoint(protocol)
        server_peer = peer.ChatServer(self.db, self.dispatcher, protocol, endpoint)
        server_peer.state_init(message)

    @staticmethod
    def bad_message(protocol, message):
        protocol.loseConnection()
        cmd = message.command
        params = message.params
        log.err(f'Received {cmd} with params: {params}')


class AIConnector:
    def __init__(self):
        from twisted.internet import reactor
        self.ai_endpoint = TCP4ClientEndpoint(reactor, config.ai_server_host,
                                              config.ai_server_port)

    def send_msg(self, msg):
        def gotProtocol(p):
            p.sendLine(msg)
            p.loseConnection()

        d = connectProtocol(self.ai_endpoint, comm.BaseProtocol())
        d.addCallback(gotProtocol)


class ChatServer(service.Service):
    def __init__(self, db):
        self.db = db
        self.dispatcher = dispatch.Dispatcher()
        self.ai_conn = AIConnector()
        self.peer_factory = PeerFactory(self.db, self.dispatcher, self.ai_conn)

    def startService(self):
        from twisted.internet import reactor
        reactor.listenTCP(config.chat_server_port,
                          self.peer_factory,
                          interface=config.chat_server_host)

    def stopService(self):
        pass
