import twisted.internet.defer as defer
from twisted.python import log, failure

from chat import irc


class InitialEndpoint(irc.IRCEndpoint):
    def __init__(self, endpoint_manager, protocol):
        super().__init__(protocol)
        self.endpoint_manager = endpoint_manager

    def irc_REGISTER(self, message):
        self.endpoint_manager.chat_client_connected(self._protocol, message)

    def irc_LOGIN(self, message):
        self.endpoint_manager.chat_client_connected(self._protocol, message)

    def irc_CONNECT(self, message):
        self.endpoint_manager.chat_server_connected(self._protocol, message)

    def irc_unknown(self, message):
        self._protocol.transport.loseConnection()
        cmd = message.command
        params = message.params
        log.err(f'ERR: bad opening message: {cmd} with params: {params}')


class ServerEndpoint(irc.IRC):
    def __init__(self, server, protocol):
        super().__init__(protocol)
        self.server = server

    def on_user_registered(self, user, mail, password):
        # TODO: check if account available, add or clash
        pass

    def server_connected(self, password):
        self.server.dispatcher.server_connected(self)

    def server_disconnected(self):
        self.server.dispatcher.server_disconnected(self)


class ClientEndpoint(irc.IRC):

    # States of client connection.
    INITIAL = 0
    REGISTERING = 1
    LOGGING_IN = 2
    LOGGED_IN = 3
    CONVERSATION = 4

    # Acceptable messages in different states.
    admissible = {
        INITIAL: {'REGISTER', 'LOGIN'},
        REGISTERING: {'PASSWORD'},
        LOGGING_IN: {'PASSWORD'},
        LOGGED_IN: {'UNREGISTER', 'LOGOUT', 'LIST', 'ISON', 'CONNECT', 'DISCONNECT',
                    'CREATE', 'DELETE', 'JOIN', 'QUIT', 'ADD', 'KICK'},
        CONVERSATION: {'DELETE', 'LEAVE', 'QUIT', 'ADD', 'KICK', 'NAMES', 'MSG'}
    }

    def __init__(self, db, dispatcher, protocol):
        super().__init__(protocol)
        self.state = self.INITIAL
        self.db = db
        self.dispatcher = dispatcher
        self.reg_deferred = None
        self.login_deferred = None

        self.nick = None
        self.password_retry = 3

    def should_handle(self, message):
        return message.command in self.admissible[self.state]

    def handle_message(self, message):
        if self.should_handle(message):
            super().handle_message(message)
        else:
            if self.state == self.INITIAL:
                self.close_connection('Incorrect opening message.')
            elif self.state == self.REGISTERING:
                if self.password_retry > 0:
                    self.warn('Provide password.')
                    self.password_retry -= 1
                else:
                    self.close_connection('Password message expected.')
            elif self.state == self.LOGGING_IN:
                if self.password_retry > 0:
                    self.warn('Provide password.')
                    self.password_retry -= 1
                else:
                    self.close_connection('Password message expected.')
            elif self.state == self.LOGGED_IN:
                # Ignore it.
                log.err(f'Incorrect message: {message.command}')
            else:
                # Ignore it.
                log.err(f'Incorrect message: {message.command}')

    def close_connection(self, communicate):
        self.connection_closed(communicate)
        self._protocol.transport.loseConnection()
        self._protocol.endpoint = None
        self._protocol = None

    @defer.inlineCallbacks
    def register_user(self, nick, mail):
        log.msg(f'REGISTERING {nick} {mail}')

        try:
            nick_available, mail_available = yield self.db.account_available(nick, mail)
            if nick_available and mail_available:
                @defer.inlineCallbacks
                def on_password_received(password):
                    try:
                        yield self.db.add_user(nick, mail, password)

                        self.state = self.LOGGED_IN
                        self.nick = nick
                        self.registered(nick, mail, password)
                        self.dispatcher.user_registered(nick, mail, password)
                    except failure.Failure:
                        self.internal_error('DB error, please try again.')

                self.reg_deferred = defer.Deferred()
                self.reg_deferred.addCallback(on_password_received)

                self.state = self.REGISTERING
                self.send_me_password()
            else:
                if not mail_available:
                    self.taken(mail, 'mail')
                else:
                    self.taken(nick, 'nick')
        except failure.Failure:
            self.internal_error('DB error, please try again.')

    @defer.inlineCallbacks
    def login_user(self, nick):
        log.msg(f'LOGGING IN {nick}')

        try:
            user_registered = yield self.db.is_user_registered(nick)
            if user_registered:
                @defer.inlineCallbacks
                def on_password_received(password):
                    try:
                        password_correct = yield self.db.password_correct(nick, password)
                        if password_correct:
                            self.state = self.LOGGED_IN
                            self.nick = nick
                            self.logged_in(nick)
                            self.dispatcher.user_logged_in(nick)
                        else:
                            # TODO: some trial countdown!
                            self.wrong_password()
                            self.login_deferred = defer.Deferred()
                            self.login_deferred.addCallback(on_password_received)
                    except failure.Failure:
                        self.internal_error('DB error, please try again.')

                self.login_deferred = defer.Deferred()
                self.login_deferred.addCallback(on_password_received)

                self.state = self.LOGGING_IN
                self.send_me_password()
            else:
                self.no_user(nick)
        except failure.Failure:
            self.internal_error('DB error, please try again.')

    def password_received(self, password):
        if self.state == self.REGISTERING:
            d, self.reg_deferred = self.reg_deferred, None
            d.callback(password)
        elif self.state == self.LOGGING_IN:
            d, self.login_deferred = self.login_deferred, None
            d.callback(password)
        else:
            log.err('ERR: PASSWORD received unexpectedly.')  # TODO: anything else?

    def logout_user(self):
        self.logged_out(self.nick)
        self.dispatcher.user_logged_out(self.nick)
        self.close_connection('Logged out.')

    @defer.inlineCallbacks
    def unregister_user(self):
        try:
            yield self.db.delete_user(self.nick)
            self.unregistered(self.nick)
            self.dispatcher.user_unregistered(self.nick)
            self.close_connection('Unregistered.')
        except failure.Failure:
            self.internal_error('DB error, please try again.')

    def get_users_status(self, users):
        users_on = self.dispatcher.is_on(users)
        self.is_on(users_on)
