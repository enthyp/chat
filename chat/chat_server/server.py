import twisted.internet.protocol as protocol

from chat import irc
from chat.chat_server.endpoints import InitialEndpoint, ClientEndpoint, ServerEndpoint


class Dispatcher:
    # TODO: could be implemented with Redis key-value store?
    def __init__(self, server):
        self.server = server
        self.direct_clients = set()  # TODO: nick -> endpoint maps?
        self.all_clients = set()
        self.chat_server_endpoints = set()
        self.channel2endpoint = {}

    def is_on(self, nicks):
        return nicks & self.all_clients

    def user_logged_in(self, nick, direct=True):
        if direct:
            self.direct_clients.add(nick)
        else:
            self.all_clients.add(nick)

    def user_logged_out(self, nick, direct=True):
        if direct:
            self.direct_clients.remove(nick)
        else:
            self.all_clients.remove(nick)

    def server_connected(self, endpoint):
        self.chat_server_endpoints.add(endpoint)

    def server_disconnected(self, endpoint):
        self.chat_server_endpoints.remove(endpoint)

    def user_registered(self, nick, mail, password):
        for peer in self.chat_server_endpoints:
            peer.registered(nick, mail, password)


class ChatServer(protocol.Factory):
    protocol = irc.IRCBaseProtocol

    def __init__(self, db):
        self.db = db
        self.dispatcher = Dispatcher(self)

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
        endpoint = ClientEndpoint(self, protocol)
        protocol.endpoint = endpoint
        endpoint.handle_message(message)
        # TODO: add to some collection of peers.

    def account_available(self, nick, mail):
        return self.db.account_available(nick, mail)

    def user_registered(self, nick):
        return self.db.user_registered(nick)

    def add_user(self, nick, mail, password):
        return self.db.add_user(nick, mail, password)

    def delete_user(self, nick):
        return self.db.delete_user(nick)

    def password_correct(self, nick, password):
        return self.db.password_correct(nick, password)
