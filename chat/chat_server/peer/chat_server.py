from twisted.python import log

import chat.chat_server.peer as peer


class InitialState(peer.State):
    def msg_CONNECT(self, message):
        self.state_manager.state_connected(message)

    def msg_unknown(self, message):
        self.state_manager.lose_connection()
        cmd = message.command
        params = message.params
        log.err(f'ERR: bad opening message: {cmd} with params: {params}')


class ConnectedState(peer.State):
    def msg_DISCONNECT(self, message):
        self.state_manager.state_disconnected(message)

    def msg_SYNC(self, message):
        # TODO: implement this + others...
        pass


class ChatServer(peer.Peer):
    def state_init(self):
        self.state = InitialState(self.protocol, self)

    def state_connected(self, message):
        self.state = ConnectedState(self.protocol, self)

    def state_disconnected(self, message):
        self.state = None
        self.lose_connection()
        # TODO: anything else?
