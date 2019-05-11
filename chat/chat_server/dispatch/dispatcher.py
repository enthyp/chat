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
        # TODO: maybe we should have a separate online users registry (users online per channel also, etc.)?
        self.users_online = set()
        self.peers = set()
        self.server_channel = dispatch.Channel('chat_servers')
        self.channels = {}

    @log_operation
    def add_peer(self, peer):
        self.peers.add(peer)

    # TODO: remove peer when done.

    @log_operation
    def is_on(self, nicks):
        return list(set(nicks) & self.users_online)

    @log_operation
    def on_user_logged_in(self, nick):
        self.users_online.add(nick)

    @log_operation
    def on_user_logged_out(self, nick):
        self.users_online.remove(nick)

    @log_operation
    def on_server_connected(self, peer):
        self.peers.add(peer)

    @log_operation
    def on_server_disconnected(self, peer):
        self.peers.remove(peer)

    @log_operation
    def user_registered(self, nick, mail, password):
        self.users_online.add(nick)

    @log_operation
    def user_logged_in(self, nick):
        self.users_online.add(nick)

    @log_operation
    def user_logged_out(self, nick):
        self.users_online.remove(nick)

    @log_operation
    def user_unregistered(self, nick):
        self.users_online.remove(nick)

    @log_operation
    def subscribe(self, channel_name, peer):
        channel = self.channels.get(channel_name, None)
        if channel:
            channel.register_subscriber(peer)

    @log_operation
    def publish(self, channel_name, message):
        channel = self.channels.get(channel_name, None)
        if channel:
            channel.publish(message)
