from chat import communication as comm
from chat.chat_server import peer


class ChatServerEndpoint(comm.Endpoint):
    def registered(self, nick, mail, password):  # ok
        self.send(f'OK_REG {nick} {mail} {password}')

    def reg_clashed(self, value, what='nick'):  # ok
        if what == 'nick':
            self.send(f'ERR_CLASH_REG nick {value}')
        elif what == 'mail':
            self.send(f'ERR_CLASH_REG mail {value}')
        else:
            raise ValueError('"what" parameter must be either "nick" or "mail".')

    def unregistered(self, user):  # ok
        self.send(f'OK_UNREG {user}')

    def logged_in(self, user):  # ok
        self.send(f'OK_LOGIN {user}')

    def login_clashed(self, user):  # ok
        self.send(f'ERR_CLASH_LOGIN {user}')

    def logged_out(self, nick):  # ok
        self.send(f'OK_LOGOUT {nick}')

    def created(self, channel, creator, users):
        users = ' '.join(users)
        self.send(f'OK_CREATED {channel} {creator} {users}')

    def channel_clashed(self, channel):
        self.send(f'ERR_CLASH_CREAT {channel}')

    def channel_deleted(self, channel):
        self.send(f'OK_DELETED {channel}')

    def user_joined(self, channel, user):
        self.send(f'JOINED {channel} {user}')

    def user_left(self, channel, user):
        self.send(f'LEFT {channel} {user}')

    def user_quit(self, channel, user):
        self.send(f'USER_QUIT {channel} {user}')

    def users_added(self, channel, users):
        users = ' '.join(users)
        self.send(f'ADDED {channel} {users}')

    def user_kicked(self, channel, users):
        users = ' '.join(users)
        self.send(f'KICKED {channel} {users}')

    def msg(self, from_user, channel, content):
        self.send(f':{from_user} MSG {channel} :{content}')

    def notify(self, reason, notification):
        self.send(f'NOTIFY {reason} :{notification}')

    def connection_closed(self, message):
        self.send(f'CLOSED :{message}')


class InitialState(peer.State):
    def msg_CONNECT(self, message):
        self.state_manager.state_connected(message)


class ConnectedState(peer.State):
    def msg_DISCONNECT(self, message):
        self.state_manager.state_disconnected(message)

    def msg_SYNC(self, message):
        # TODO: implement this + others...
        pass


class ChatServer(peer.Peer):
    def state_init(self, message):
        self.state = InitialState(self.protocol, self.endpoint, self)
        self.state.handle_message(message)

    def state_connected(self, message):
        self.state = ConnectedState(self.protocol, self.endpoint, self)
        self.state.handle_message(message)

    def state_disconnected(self, _):
        self.state = None
        self.lose_connection()
        # TODO: anything else?
