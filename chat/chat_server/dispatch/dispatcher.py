from functools import wraps
from twisted.python import log


def log_operation(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        log.msg(f'DISPATCH: {method.__name__} CALLED')
        return method(*args, **kwargs)

    return wrapper


# TODO: IDEA!!! Dispatcher can have a collection of Channel objects! each Channel
# is responsible for message distribution.

class Dispatcher:
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
