# Partially based on twisted.words.irc
from abc import ABC, abstractmethod

from twisted.protocols import basic
from twisted.python import log


class IRCBadMessageFormat(Exception):
    """Incorrect message format."""
    pass


class IRCMessage:
    """IRC message representation."""

    def __init__(self, string):
        prefix, command, params = self._parse_message(string)
        self.prefix = prefix
        self.command = command
        self.params = params

    @staticmethod
    def _parse_message(string):
        if not string:
            raise IRCBadMessageFormat('Empty string.')

        prefix, trailing = '', ''
        if string[0] == ':':
            prefix, string = string[1:].split(' ', 1)
        if ':' in string:
            string, trailing = string.split(':', 1)

        if not string:
            raise IRCBadMessageFormat('No command.')

        args = string.split()
        if trailing:
            args.append(trailing)

        return prefix, args[0], args[1:]

    def __str__(self):  # TODO: necessary?
        string = ' '.join([self.command] + self.params)
        if self.prefix:
            string = f':{self.prefix} {string}'

        return string


class IRCProtocol(basic.LineReceiver):
    """
    Physical connection to client who communicates via IRC messages.

    All handling of incoming messages, as well as initiating message
    sends is done at IRCEndpoint level.

    """

    delimiter = '\n'.encode('utf-8')

    # Low-level protocol methods.
    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')
        try:
            message = IRCMessage(line)
            self.handler.handle_message(message)
        except IRCBadMessageFormat as e:
            log.err(f'ERR: Exception: {str(e)} caused by line: {line}')

    def sendLine(self, line):
        line = line.encode('utf-8', errors='ignore')
        super().sendLine(line)

    @property
    def handler(self):
        return self._handler

    @handler.setter
    def handler(self, handler):
        self._handler = handler


class Handler(ABC):
    @abstractmethod
    def handle_message(self, message):
        pass
    

class ProtocolAdapter(ABC, Handler):
    @abstractmethod
    def send(self, content):
        pass


class IRCAdapter(ProtocolAdapter):
    """
    Interface of individual IRCProtocol instance.

    It should define methods that allow for sending appropriate IRC messages,
    as well as handler methods that get called when IRC message is received.

    """

    def __init__(self, protocol):
        self._protocol = protocol

    def send(self, line):
        self._protocol.sendLine(line)

    def handle_message(self, message):
        method_name = f'irc_{message.command}'
        method = getattr(self, method_name, None)

        try:
            if method is None:
                self.irc_unknown(message)
            else:
                method(message)
        except Exception as e:
            log.err(f'ERR: Exception: {str(e)} in method call {method.__name__}')

    @staticmethod
    def irc_unknown(message):
        cmd = message.command
        params = ' '.join(message.params)
        log.err(f'ERR: Unknown command: {cmd} with params: {params}')


class IRCServerAdapter(IRCAdapter):
    # Outgoing messages (server -> client).
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

    def wrong_password(self):
        self.send('ERR_BAD_PASSWORD')

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

    # Outgoing messages (server -> server).
    def connect(self, password):
        self.send(f'CONNECT {password}')

    def disconnect(self):
        self.send('DISCONNECT')

    def sync(self):
        self.send('SYNC')

    # TODO: handle incomplete parameters?
    # Incoming commands.
    def irc_REGISTER(self, message):  # ok
        # TODO: check if user and mail are syntactically correct?
        user, mail = message.params
        self.register_user(user, mail)

    def irc_OK_REG(self, message):
        user, mail, password = message.params
        self.on_user_registered(user, mail, password)

    def irc_ERR_CLASH_REG(self, message):  # ok
        what, value = message.params
        if what in ('nick', 'mail'):
            self.on_reg_clashed(what, value)
        else:
            log.err(f'ERR: ERR_CLASH_REG message with incorrect reason: {what}')

    def irc_OK_UNREG(self, message):  # ok
        user = message.params[0]
        self.on_user_unregistered(user)

    def irc_LOGIN(self, message):  # ok
        user = message.params[0]
        self.login_user(user)

    def irc_OK_LOGIN(self, message):  # ok
        user = message.params[0]
        self.on_user_logged_in(user)

    def irc_ERR_CLASH_LOGIN(self, message):  # ok
        user = message.params[0]
        self.on_login_clashed(user)

    def irc_PASSWORD(self, message):  # ok
        password = message.params[0]
        self.password_received(password)

    def irc_UNREGISTER(self, _):  # ok
        self.unregister_user()

    def irc_LOGOUT(self, _):  # ok
        self.logout_user()

    def irc_OK_LOGOUT(self, message):  # ok
        user = message.params[0]
        self.on_user_logged_out(user)

    def irc_LIST(self, _):  # ok
        self.get_channel_list()

    def irc_ISON(self, message):  # ok
        users = message.params
        self.get_users_status(users)

    def irc_CREATE(self, message):
        channel, mode = message.params[:2]
        if mode in ('priv', 'pub'):
            users = message.params[2:]
            self.create_channel(channel, mode == 'priv', users)
        else:
            log.err(f'ERR: CREATE message with incorrect mode: {mode}')

    def irc_OK_CREATED(self, message):
        channel, creator = message.params[:2]
        users = message.params[2:]
        self.on_channel_created(channel, creator, users)

    def irc_ERR_CLASH_CREAT(self, message):
        channel = message.params[0]
        self.on_creation_clashed(channel)

    def irc_DELETE(self, message):
        channel = message.params[0]
        self.delete_channel(channel)

    def irc_OK_DELETED(self, message):
        channel = message.params[0]
        self.on_channel_deleted(channel)

    def irc_JOIN(self, message):
        channel = message.params[0]
        self.join_channel(channel)

    def irc_JOINED(self, message):
        channel, user = message.params
        self.on_user_joined(channel, user)

    def irc_LEAVE(self, message):
        channel = message.params[0]
        self.leave_channel(channel)

    def irc_LEFT(self, message):
        channel, user = message.params
        self.on_user_left(channel, user)

    def irc_QUIT(self, message):
        channel = message.params[0]
        self.quit_channel(channel)

    def irc_USER_QUIT(self, message):
        channel, user = message.params
        self.on_user_quit(channel, user)

    def irc_ADD(self, message):
        channel = message.params[0]
        users = message.params[1:]
        self.add_to_channel(channel, users)

    def irc_ADDED(self, message):
        channel = message.params[0]
        users = message.params[1:]
        self.on_users_added(channel, users)

    def irc_KICK(self, message):
        channel = message.params[0]
        users = message.params[1:]
        self.kick_from_channel(channel, users)

    def irc_KICKED(self, message):
        channel = message.params[0]
        users = message.params[1:]
        self.on_users_kicked(channel, users)

    def irc_NAMES(self, message):
        channel = message.params[0]
        self.get_users_on_channel(channel)

    def irc_MSG(self, message):
        from_user = message.prefix
        channel = message.params[0]
        content = message.params[1]
        self.message_received(from_user, channel, content)

    def irc_CONNECT(self, message):
        password = message.params[0]
        self.server_connected(password)

    def irc_DISCONNECT(self, _):
        self.server_disconnected()

    def irc_SYNC(self, _):
        self.sync_requested()

    # Endpoints to implement server reactions.
    def register_user(self, user, mail):  # ok
        pass

    def on_user_registered(self, user, mail, password):
        pass

    def on_reg_clashed(self, what, value):
        pass

    def on_user_unregistered(self, user):
        pass

    def login_user(self, user):  # ok
        pass

    def on_user_logged_in(self, user):  # ok
        pass

    def on_login_clashed(self, user):
        pass

    def password_received(self, password):  # ok
        pass

    def unregister_user(self):
        pass

    def logout_user(self):
        pass

    def on_user_logged_out(self, user):
        pass

    def get_channel_list(self):  # ok
        pass

    def get_users_status(self, users):  # ok
        pass

    def create_channel(self, channel, private, users):
        pass

    def on_channel_created(self, channel, creator, users):
        pass

    def on_creation_clashed(self, channel):
        pass

    def delete_channel(self, channel):
        pass

    def on_channel_deleted(self, channel):
        pass

    def join_channel(self, channel):
        pass

    def on_user_joined(self, channel, user):
        pass

    def leave_channel(self, channel):
        pass

    def on_user_left(self, channel, user):
        pass

    def quit_channel(self, channel):
        pass

    def on_user_quit(self, channel, user):
        pass

    def add_to_channel(self, channel, users):
        pass

    def on_users_added(self, channel, users):
        pass

    def kick_from_channel(self, channel, users):
        pass

    def on_users_kicked(self, channel, users):
        pass

    def get_users_on_channel(self, channel):
        pass

    def message_received(self, from_user, channel, content):
        pass

    def server_connected(self, password):
        pass

    def server_disconnected(self):
        pass

    def sync_requested(self):
        pass


class IRCClientAdapter(IRCAdapter):
    # Outgoing commands.
    def register(self, user, mail):  # ok
        self.sendLine(f'REGISTER {user} {mail}')

    def login(self, user):  # ok
        self.sendLine(f'LOGIN {user}')

    def password(self, password):  # ok
        self.sendLine(f'PASSWORD {password}')

    def unregister(self):  # ok
        self.sendLine('UNREGISTER')

    def logout(self):  # ok
        self.sendLine('LOGOUT')

    def list(self):  # ok
        self.sendLine('LIST')

    def is_on(self, nicks):  # ok
        nick_list = ' '.join(nicks)
        self.sendLine(f'ISON {nick_list}')

    def create(self, channel, nicks, private=False):
        nick_list = ' '.join(nicks)
        mode = 'priv' if private else 'pub'
        self.sendLine(f'CREATE {channel} {mode} {nick_list}')

    def delete(self, channel):
        self.sendLine(f'DELETE {channel}')

    def join(self, channel):
        self.sendLine(f'JOIN {channel}')

    def leave(self, channel):
        self.sendLine(f'LEAVE {channel}')

    def quit(self, channels):
        channel_list = ' '.join(channels)
        self.sendLine(f'QUIT {channel_list}')

    # TODO: add invites to public channels!
    def add(self, channel, nicks):
        nick_list = ' '.join(nicks)
        self.sendLine(f'ADD {channel} {nick_list}')

    def kick(self, channel, nicks):
        nick_list = ' '.join(nicks)
        self.sendLine(f'KICK {channel} {nick_list}')

    def names(self, channel):
        self.sendLine(f'NAMES {channel}')

    def msg(self, channel, content):
        self.sendLine(f'MSG {channel} :{content}')

    # Incoming commands.
    # Registration.
    def irc_RPL_PWD(self, _):  # ok
        self.password_requested()

    def irc_OK_REG(self, _):  # ok
        self.registered()

    def irc_ERR_TAKEN(self, message):  # ok
        what = message.params[0]
        if what == 'nick':
            self.nick_taken()
        else:
            self.mail_in_use()

    def irc_ERR_CLASH_REG(self, message):  # ok
        what = message.params[0]
        if what == 'nick':
            self.nick_clash()
        else:
            self.mail_clash()

    def irc_ERR_INTERNAL(self, message):
        communicate = message.params[0]
        self.server_error(communicate)

    def irc_OK_UNREG(self, _):  # ok
        self.unregistered()

    # Login.
    def irc_OK_LOGIN(self, _):  # ok
        self.logged_in()

    def irc_ERR_CLASH_LOGIN(self, _):  # ok
        self.login_clash()

    def irc_ERR_BAD_PASSWORD(self):
        self.bad_password()

    def irc_OK_LOGOUT(self, _):  # ok
        self.logged_out()

    # Info.
    def irc_RPL_LIST(self, message):  # ok
        channels = message.params
        self.channels_available(channels)

    def irc_RPL_ISON(self, message):  # ok
        users = message.params
        self.users_online(users)

    def irc_RPL_NAMES(self, message):
        channel = message.params[0]
        users = message.params[1:]
        self.users_on_channel(channel, users)

    # Channel creation.
    def irc_OK_CREATED(self, message):
        channel = message.params[0]
        users = message.params[2:]
        self.channel_created(channel, users)

    def irc_ERR_EXISTS(self, message):
        channel = message.params[0]
        self.channel_exists(channel)

    def irc_ERR_CLASH_CREAT(self, message):
        channel = message.params[0]
        self.channel_clash(channel)

    # Channel removal.
    def irc_OK_DELETED(self, message):
        channel = message.params[0]
        self.channel_deleted(channel)

    def irc_ERR_NOCHANNEL(self, message):
        channel = message.params[0]
        self.no_channel(channel)

    def irc_ERR_NOPERM(self, message):
        perm_type = message.params[0]
        reason = message.params[1]
        self.no_perms(perm_type, reason)

    # Joining/leaving channels.
    def irc_OK_JOINED(self, message):
        channel = message.params[0]
        self.joined(channel)

    def irc_JOINED(self, message):
        channel = message.params[0]
        user = message.params[1]
        self.user_joined(user, channel)

    def irc_OK_LEFT(self, message):
        channel = message.params[0]
        self.left(channel)

    def irc_LEFT(self, message):
        channel = message.params[0]
        user = message.params[1]
        self.user_left(user, channel)

    def irc_OK_QUIT(self, message):
        channel = message.params[0]
        self.quit(channel)

    def irc_QUIT(self, message):
        channel = message.params[0]
        user = message.params[1]
        self.user_quit(user, channel)

    # Adding/removing users.
    def irc_OK_ADDED(self, message):
        channel = message.params[0]
        user = message.params[1]
        self.added_user(user, channel)

    def irc_ERR_NOUSER(self, message):
        user = message.params[0]
        self.no_user(user)

    def irc_OK_KICKED(self, message):
        channel = message.params[0]
        user = message.params[1]
        self.kicked_user(user, channel)

    def irc_KICKED(self, message):
        channel = message.params[0]
        user = message.params[1]
        self.user_kicked(user, channel)

    # Others.
    def irc_MSG(self, message):
        from_user = message.prefix
        channel = message.params[0]
        content = message.params[1]
        self.got_message(from_user, channel, content)

    def irc_NOTIFY(self, message):
        # TODO: different notification types (reasons)?
        reason = message.params[0]
        notification = message.params[1]
        self.notified(reason, notification)

    def irc_WARN(self, message):
        warning = message.params[0]
        self.warned(warning)

    def irc_CLOSED(self, message):
        communicate = message.params[0]
        self.connection_closed(communicate)

    # Endpoints to implement client reactions.
    # Registration.
    def password_requested(self):
        pass

    def registered(self):
        pass

    def nick_taken(self):
        pass

    def mail_in_use(self):
        pass

    def nick_clash(self):
        pass

    def mail_clash(self):
        pass

    def server_error(self, communicate):
        pass

    def unregistered(self):
        pass

    # Login.
    def logged_in(self):
        pass

    def login_clash(self):
        pass

    def bad_password(self):
        pass

    def logged_out(self):
        pass

    # Info.
    def channels_available(self, channels):  # ok
        pass

    def users_online(self, users):  # ok
        pass

    def users_on_channel(self, users, channel):
        pass

    # Channel creation.
    def channel_created(self, channel, users):
        pass

    def channel_exists(self, channel):
        pass

    def channel_clash(self, channel):
        pass

    # Channel removal.
    def channel_deleted(self, channel):
        pass

    def no_channel(self, channel):
        pass

    def no_perms(self, perm_type, reason):
        pass

    # Joining/leaving channels.
    def joined(self, channel):
        pass

    def user_joined(self, user, channel):
        pass

    def left(self, channel):
        pass

    def user_left(self, user, channel):
        pass

    def user_quit(self, user, channel):
        pass

    # Adding/removing users.
    def added_user(self, user, channel):
        pass

    def no_user(self, user):
        pass

    # TODO: action vs information
    def kicked_user(self, user, channel):
        pass

    def user_kicked(self, user, channel):
        pass

    # Others.
    def got_message(self, from_user, channel, content):
        pass

    def notified(self, reason, notification):
        pass

    def warned(self, warning):
        pass

    def connection_closed(self, communicate):
        pass
