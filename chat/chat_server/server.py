from twisted.python import log
from twisted.internet import protocol
from twisted.application import service

from chat.chat_server import config
from chat.chat_server import peer
from chat.chat_server import dispatch


class PeerFactory(protocol.Factory):

    protocol = protocol.BaseProtocol

    class InitialSubscriber:
        def __init__(self, factory, protocol):
            self.protocol = protocol
            self.factory = factory

        def handle_message(self, message):
            self.protocol.unregister_subscriber(self)

            if message.command in ('REGISTER', 'LOGIN'):
                self.factory.chat_client_connected(self.protocol, message)
            elif message.command == 'CONNECT':
                self.factory.chat_server_connected(self.protocol, message)
            else:
                self.factory.bad_message(self.protocol, message)

        def __del__(self):
            # TODO: for now.
            log.msg('Initial subscriber taken out with trash.')

    def __init__(self, db, dispatcher):
        self.db = db
        self.dispatcher = dispatcher

    def buildProtocol(self, addr):
        protocol = self.protocol()
        subscriber = self.InitialSubscriber(self, protocol)
        protocol.register_subscriber(subscriber)

        return protocol

    def chat_client_connected(self, protocol, message):
        endpoint = peer.ChatClientEndpoint(protocol)
        client_peer = peer.ChatClient(self.db, self.dispatcher, protocol, endpoint)
        client_peer.state_init(message)

        self.dispatcher.add_peer(client_peer)

    def chat_server_connected(self, protocol, message):
        endpoint = peer.ChatServerEndpoint(protocol)
        server_peer = peer.ChatServer(self.db, self.dispatcher, protocol, endpoint)
        server_peer.state_init(message)

        self.dispatcher.add_peer(server_peer)

    @staticmethod
    def bad_message(self, protocol, message):
        protocol.lose_connection()
        cmd = message.command
        params = message.params
        log.err(f'Received {cmd} with params: {params}')


class ChatServer(service.Service):
    def __init__(self, db):
        self.db = db
        self.dispatcher = dispatch.Dispatcher()
        self.peer_factory = PeerFactory(self.db, self.dispatcher)

    def startService(self):
        from twisted.internet import reactor
        reactor.listenTCP(config.server_port,
                          self.peer_factory,
                          interface=config.server_host)

    def stopService(self):
        pass
