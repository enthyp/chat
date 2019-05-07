from functools import wraps
import twisted.internet.protocol as protocol
from twisted.python import log
from twisted.application import service

from chat import irc
from chat.chat_server import config
from chat.chat_server.endpoints import InitialEndpoint, ClientEndpoint, ServerEndpoint


def log_operation(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        log.msg(f'DISPATCH: {method.__name__} CALLED')
        return method(*args, **kwargs)

    return wrapper


class Dispatcher:
    # TODO: could be implemented with Redis key-value store + txredis?
    def __init__(self):
        self.direct_clients = set()  # TODO: nick -> (client/server) endpoint maps?
        self.all_clients = set()
        self.chat_server_endpoints = set()
        self.channel2endpoint = {}

    @log_operation
    def is_on(self, nicks):
        return list(set(nicks) & self.all_clients)

    @log_operation
    def on_user_logged_in(self, nick, direct=True):
        if direct:
            self.direct_clients.add(nick)
        else:
            self.all_clients.add(nick)

    @log_operation
    def on_user_logged_out(self, nick, direct=True):
        if direct:
            self.direct_clients.remove(nick)
        else:
            self.all_clients.remove(nick)

    @log_operation
    def on_server_connected(self, endpoint):
        self.chat_server_endpoints.add(endpoint)

    @log_operation
    def on_server_disconnected(self, endpoint):
        self.chat_server_endpoints.remove(endpoint)

    @log_operation
    def user_registered(self, nick, mail, password):
        for peer in self.chat_server_endpoints:
            peer.registered(nick, mail, password)
        self.direct_clients.add(nick)
        self.all_clients.add(nick)

    @log_operation
    def user_logged_in(self, nick):
        for peer in self.chat_server_endpoints:
            peer.logged_in(nick)
        self.direct_clients.add(nick)
        self.all_clients.add(nick)

    @log_operation
    def user_unregistered(self, nick):
        for peer in self.chat_server_endpoints:
            peer.unregistered(nick)
        self.direct_clients.remove(nick)
        self.all_clients.remove(nick)

    @log_operation
    def user_logged_out(self, nick):
        for peer in self.chat_server_endpoints:
            peer.logged_out(nick)
        self.direct_clients.remove(nick)
        self.all_clients.remove(nick)


class EndpointManager(protocol.Factory):
    protocol = irc.IRCProtocol

    def __init__(self, db, dispatcher):
        self.db = db
        self.dispatcher = dispatcher

    def buildProtocol(self, addr):
        protocol = self.protocol()
        endpoint = InitialEndpoint(self, protocol)
        protocol.endpoint = endpoint

        return protocol

    def chat_server_connected(self, protocol, message):
        endpoint = ServerEndpoint(self, protocol)
        protocol.endpoint = endpoint
        endpoint.handle_message(message)

    def chat_client_connected(self, protocol, message):
        endpoint = ClientEndpoint(self.db, self.dispatcher, protocol)
        protocol.endpoint = endpoint
        endpoint.handle_message(message)
        # TODO: add to some collection of peers.


class ChatServer(service.Service):
    def __init__(self, db):
        self.db = db
        self.dispatcher = Dispatcher()
        self.endpoint_manager = EndpointManager(self.db, self.dispatcher)

    def startService(self):
        from twisted.internet import reactor
        reactor.listenTCP(config.server_port,
                          self.endpoint_manager,
                          interface=config.server_host)

    def stopService(self):
        pass
