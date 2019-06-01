from functools import wraps
from twisted.python import log

from chat.chat_server import dispatch
from chat.chat_server.peer import ChatClient, ChatServer


def log_operation(method):
    @wraps(method)
    def wrapper(*args, **kwargs):
        log.msg(f'DISPATCH: {method.__name__} CALLED')
        return method(*args, **kwargs)

    return wrapper


class Dispatcher:
    def __init__(self, channels=None):
        self.user2peer = {}
        self.server_peers = set()
        self.channels = {}

        if channels:
            for ch_name in channels:
                self.add_channel(ch_name)

    @log_operation
    def add_peer(self, peer, nick=None):
        if nick:
            self.user2peer[nick] = peer
        else:
            self.server_peers.add(peer)

    # pretty terrible, short on time
    @log_operation
    def remove_peer(self, peer, nick=None):
        if isinstance(peer, ChatClient):
            if not nick:
                for k, v in self.user2peer.items():
                    if v == peer:
                        nick = k
                        break
            self.user2peer.pop(nick, None)

            for c in self.channels.values():
                c.unregister_user(nick)
        elif isinstance(peer, ChatServer):
            nicks = []
            for k, v in self.user2peer.items():
                if v == peer:
                    nicks.append(k)
            self.server_peers.remove(peer)
            for n in nicks:
                self.user2peer.pop(n, None)

    @log_operation
    def add_channel(self, channel_name, replace=True):
        if channel_name not in self.channels.keys() or replace:
            self.channels[channel_name] = dispatch.Channel(self, channel_name)

    @log_operation
    def remove_channel(self, channel_name):
        self.channels.pop(channel_name, None)

    @log_operation
    def is_on(self, nicks):
        return list(set(nicks) & set(self.user2peer.keys()))

    @log_operation
    def names(self, channel_name):
        channel = self.channels.get(channel_name, None)
        return channel.names() if channel else set()

    @log_operation
    def subscribe(self, channel_name, nick):
        channel = self.channels.get(channel_name, None)
        if channel:
            channel.register_user(nick)

    @log_operation
    def unsubscribe(self, channel_name, nick):
        channel = self.channels.get(channel_name, None)
        if channel:
            channel.unregister_user(nick)

    @log_operation
    def get_peers(self, names, local_only=True):
        peers = [self.user2peer[nick] for nick in names if nick in names]
        if local_only:
            peers = [p for p in peers if isinstance(p, ChatClient)]

        return set(peers)

    @log_operation
    def publish(self, channel_name, author, message, locally=False):
        if channel_name == 'servers':
            for s in self.server_peers - {author}:
                s.receive(message)
        else:
            channel = self.channels.get(channel_name, None)
            if channel:
                channel.publish(author, message, locally)

    @log_operation
    def notify(self, nick, notification):
        peer = self.user2peer[nick]
        peer.receive(notification)
