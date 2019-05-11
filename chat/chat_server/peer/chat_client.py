from twisted.python import failure
import twisted.internet.defer as defer

from chat import communication as comm
from chat.chat_server import peer


class ChatClientEndpoint(comm.Endpoint):
    def send_me_password(self):  # ok
        self.send('RPL_PWD')

    def registered(self, nick, mail, password):  # ok
        self.send(f'OK_REG {nick} {mail} {password}')

    def taken(self, value, what='nick'):  # ok
        if what == 'nick':
            self.send(f'ERR_TAKEN nick {value}')
        elif what == 'mail':
            self.send(f'ERR_TAKEN mail {value}')
        else:
            raise ValueError('"what" parameter must be either "nick" or "mail".')

    def reg_clashed(self, value, what='nick'):  # ok
        if what == 'nick':
            self.send(f'ERR_CLASH_REG nick {value}')
        elif what == 'mail':
            self.send(f'ERR_CLASH_REG mail {value}')
        else:
            raise ValueError('"what" parameter must be either "nick" or "mail".')

    def internal_error(self, communicate):
        self.send(f'ERR_INTERNAL :{communicate}')

    def unregistered(self, user):  # ok
        self.send(f'OK_UNREG {user}')

    def logged_in(self, user):  # ok
        self.send(f'OK_LOGIN {user}')

    def login_clashed(self, user):  # ok
        self.send(f'ERR_CLASH_LOGIN {user}')

    def wrong_password(self, count):
        self.send(f'ERR_BAD_PASSWORD {str(count)}')

    def logged_out(self, nick):  # ok
        self.send(f'OK_LOGOUT {nick}')

    def list(self, channels):  # ok
        channels = ' '.join(channels)
        self.send(f'RPL_LIST {channels}')

    def is_on(self, users):  # ok
        users = ' '.join(users)
        self.send(f'RPL_ISON {users}')

    def names(self, channel, users):
        users = ' '.join(users)
        self.send(f'RPL_NAMES {channel} {users}')

    def created(self, channel, creator, users):
        users = ' '.join(users)
        self.send(f'OK_CREATED {channel} {creator} {users}')

    def channel_exists(self, channel):
        self.send(f'ERR_EXISTS {channel}')

    def channel_clashed(self, channel):
        self.send(f'ERR_CLASH_CREAT {channel}')

    def channel_deleted(self, channel):
        self.send(f'OK_DELETED {channel}')

    def no_channel(self, channel):
        self.send(f'ERR_NOCHANNEL {channel}')

    def no_perms(self, perm_type, reason):
        self.send(f'ERR_NO_PERM {perm_type} :{reason}')

    def joined(self, channel):
        self.send(f'OK_JOINED {channel}')

    def user_joined(self, channel, user):
        self.send(f'JOINED {channel} {user}')

    def left(self, channel):
        self.send(f'OK_LEFT {channel}')

    def user_left(self, channel, user):
        self.send(f'LEFT {channel} {user}')

    def quit(self, channel):
        self.send(f'OK_QUIT {channel}')

    def user_quit(self, channel, user):
        self.send(f'USER_QUIT {channel} {user}')

    def added(self, channel, users):
        users = ' '.join(users)
        self.send(f'OK_ADDED {channel} {users}')

    def users_added(self, channel, users):
        users = ' '.join(users)
        self.send(f'ADDED {channel} {users}')

    def no_user(self, user):
        self.send(f'ERR_NOUSER {user}')

    def kicked(self, channel, users):
        users = ' '.join(users)
        self.send(f'OK_KICKED {channel} {users}')

    def user_kicked(self, channel, users):
        users = ' '.join(users)
        self.send(f'KICKED {channel} {users}')

    def msg(self, from_user, channel, content):
        self.send(f':{from_user} MSG {channel} :{content}')

    def notify(self, reason, notification):
        self.send(f'NOTIFY {reason} :{notification}')

    def warn(self, warning):
        self.send(f'WARN :{warning}')

    def connection_closed(self, message):
        self.send(f'CLOSED :{message}')


class InitialState(peer.State):
    def msg_REGISTER(self, message):
        self.manager.state_registering(message)

    def msg_LOGIN(self, message):
        self.manager.state_logging_in(message)


class RegisteringState(peer.State):
    def __init__(self, protocol, endpoint, db, dispatcher, manager):
        super().__init__(protocol, endpoint, manager)

        self.db = db
        self.dispatcher = dispatcher
        self.reg_deferred = None

    @defer.inlineCallbacks
    def msg_REGISTER(self, message):
        nick, mail = message.params
        self.log_msg(f'received {nick} {mail}')

        try:
            nick_available, mail_available = yield self.db.account_available(nick, mail)
            if nick_available and mail_available:
                @defer.inlineCallbacks
                def on_password_received(password):
                    try:
                        yield self.db.add_user(nick, mail, password)
                        self.manager.state_logged_in(nick)
                        self.dispatcher.user_registered(nick, mail, password)
                    except failure.Failure:
                        self.endpoint.internal_error('DB error, please try again.')

                self.reg_deferred = defer.Deferred()
                self.reg_deferred.addCallback(on_password_received)
                self.endpoint.send_me_password()
            else:
                if not mail_available:
                    self.endpoint.taken(mail, 'mail')
                else:
                    self.endpoint.taken(nick, 'nick')
        except failure.Failure:
            self.endpoint.internal_error('DB error, please try again.')

    def msg_PWD(self, message):
        password = message.params[0]
        if self.reg_deferred:
            d, self.reg_deferred = self.reg_deferred, None
            d.callback(password)


class LoggingInState(peer.State):
    def __init__(self, protocol, endpoint,db, dispatcher, manager):
        super().__init__(protocol, endpoint, manager)

        self.db = db
        self.dispatcher = dispatcher
        self.login_deferred = None
        self.password_countdown = 3

    @defer.inlineCallbacks
    def msg_LOGIN(self, message):
        nick = message.params[0]
        self.log_msg(f'{nick}')

        try:
            user_registered = yield self.db.is_user_registered(nick)
            if user_registered:
                @defer.inlineCallbacks
                def on_password_received(password):
                    try:
                        password_correct = yield self.db.password_correct(nick, password)
                        if password_correct:
                            self.manager.state_logged_in(nick)
                            self.dispatcher.user_logged_in(nick)
                        else:
                            self.password_countdown -= 1

                            if self.password_countdown > 0:
                                self.login_deferred = defer.Deferred()
                                self.login_deferred.addCallback(on_password_received)
                                self.endpoint.wrong_password(self.password_countdown)
                            else:
                                self.manager.lose_connection()
                    except failure.Failure:
                        self.endpoint.internal_error('DB error, please try again.')

                self.login_deferred = defer.Deferred()
                self.login_deferred.addCallback(on_password_received)
                self.endpoint.send_me_password()
            else:
                self.endpoint.no_user(nick)
        except failure.Failure:
            self.endpoint.internal_error('DB error, please try again.')

    def msg_PWD(self, password):
        if self.login_deferred:
            d, self.login_deferred = self.login_deferred, None
            d.callback(password)


class LoggedInState(peer.State):
    def __init__(self, protocol, endpoint, db, dispatcher, manager, nick):
        super().__init__(protocol, endpoint, manager)

        self.db = db
        self.dispatcher = dispatcher
        self.nick = nick

    def msg_LOGOUT(self, _):
        self.endpoint.logged_out(self.nick)
        self.dispatcher.user_logged_out()
        self.manager.lose_connection()

    @defer.inlineCallbacks
    def msg_UNREGISTER(self, _):
        try:
            yield self.db.delete_user(self.nick)
            self.endpoint.unregistered(self.nick)
            self.dispatcher.user_unregistered()
            self.manager.lose_connection()
        except failure.Failure:
            self.internal_error('DB error, please try again.')

    def msg_ISON(self, message):
        users = message.params
        users_on = self.dispatcher.is_on(users)
        self.endpoint.is_on(users_on)


class ChatClient(peer.Peer):
    def state_init(self, message):
        self.state = InitialState(self.protocol, self.endpoint, self)
        self.state.handle_message(message)

    def state_registering(self, message):
        self.state = RegisteringState(self.protocol, self.endpoint,
                                      self.db, self.dispatcher, self)
        self.state.handle_message(message)

    def state_logging_in(self, message):
        self.state = LoggingInState(self.protocol, self.endpoint,
                                    self.db, self.dispatcher, self)
        self.state.handle_message(message)

    def state_logged_in(self, nick):
        self.state = LoggedInState(self.protocol, self.endpoint,
                                   self.db, self.dispatcher, self,
                                   nick)
