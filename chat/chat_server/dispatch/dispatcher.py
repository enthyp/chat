from functools import wraps
from twisted.python import log

from chat.chat_server import dispatch


def log_operation(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        log.msg(f'DISPATCH: {method.__name__} CALLED')
        return method(*args, **kwargs)

    return wrapper


class Dispatcher:
    def __init__(self):
        self.users = set()
        self.direct_users = {}  # nick -> Peer
        self.channels = {'servers': dispatch.Channel()}

    @log_operation
    def add_user(self, nick):
        self.users.add(nick)

    @log_operation
    def remove_user(self, nick):
        self.users.remove(nick)

    @log_operation
    def add_server(self, server_peer):
        self.channels['servers'].register_peer(server_peer)

    @log_operation
    def remove_server(self, server_peer):
        self.channels['servers'].unregister_peer(server_peer)

    @log_operation
    def add_channel(self, channel_name, replace=True):
        if channel_name not in self.channels.keys() or replace:
            self.channels[channel_name] = dispatch.Channel(channel_name)

    @log_operation
    def remove_channel(self, channel_name):
        try:
            del self.channels[channel_name]
        except KeyError:
            pass

    @log_operation
    def is_on(self, nicks):
        return list(set(nicks) & self.users)

    @log_operation
    def names(self, channel_name):
        channel = self.channels.get(channel_name, None)
        return channel.names() if channel else None

    @log_operation
    def subscribe(self, channel_name, peer):
        channel = self.channels.get(channel_name, None)
        if channel:
            channel.register_peer(peer)

    @log_operation
    def publish(self, channel_name, author, message):
        channel = self.channels.get(channel_name, None)
        if channel:
            channel.publish(author, message)

    @log_operation
    def direct(self, nick, message):
        self.direct_users[nick].receive(message)
