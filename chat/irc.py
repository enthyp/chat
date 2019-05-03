# Based on twisted.words.irc
from twisted.protocols import basic
from twisted.python import log


class IRCBadMessage(Exception):
    """Incorrect message format."""
    pass


class IRCMessage:
    def __init__(self, string):
        prefix, command, params = self._parse_message(string)
        self.prefix = prefix
        self.command = command
        self.params = params

    @staticmethod
    def _parse_message(string):
        if not string:
            raise IRCBadMessage('Empty string.')

        prefix, trailing = '', ''
        if string[0] == ':':
            prefix, string = string[1:].split(' ', 1)
        if ':' in string:
            string, trailing = string.split(':', 1)

        if not string:
            raise IRCBadMessage('No command.')

        args = string.split()
        if trailing:
            args.append(trailing)

        return prefix, args[0], args[1:]

    def __str__(self):  # TODO: necessary?
        string = ' '.join([self.command] + self.params)
        if self.prefix:
            string = f':{self.prefix} {string}'

        return string


class IRCBase(basic.LineReceiver):
    # Low-level protocol methods.
    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')
        try:
            message = IRCMessage(line)
            self.handle_message(message)
        except IRCBadMessage as e:
            self.bad_message(line, e)

    def sendLine(self, line):
        line = line.encode('utf-8', errors='ignore')
        super().sendLine(line)

    # Initial handling.
    def handle_message(self, message):
        method_name = f'irc_{message.command}'
        method = getattr(self, method_name, None)

        if method is None:
            self.irc_unknown(message)
        else:
            method(message)

    @staticmethod
    def irc_unknown(message):
        cmd = message.command
        params = ' '.join(message.params)
        log.err(f'Unknown command: {cmd} with params: {params}')

    @staticmethod
    def bad_message(line, exception):
        log.err(f'Exception: {str(exception)} caused by line: {line}')


class IRC(IRCBase):
    # Outgoing messages (server -> client).
    def send_me_password(self):
        self.sendLine('RPL_PWD')

    def registered(self, nick, mail, password):
        self.sendLine(f'OK_REG {nick} {mail} {password}')

    def taken(self, value, what='nick'):
        if what == 'nick':
            self.sendLine(f'ERR_TAKEN nick {value}')
        elif what == 'mail':
            self.sendLine(f'ERR_TAKEN mail {value}')
        else:
            raise ValueError('"what" parameter must be either "nick" or "mail".')

    def reg_clashed(self, value, what='nick'):
        if what == 'nick':
            self.sendLine(f'ERR_CLASH_REG nick {value}')
        elif what == 'mail':
            self.sendLine(f'ERR_CLASH_REG mail {value}')
        else:
            raise ValueError('"what" parameter must be either "nick" or "mail".')

    def unregistered(self, nick):
        self.sendLine(f'OK_UNREG {nick}')

    def logged_in(self, nick):
        self.sendLine(f'OK_LOGIN {nick}')

    def login_clashed(self, nick):
        self.sendLine(f'ERR_CLASH_LOGIN {nick}')

    def logged_out(self, nick):
        self.sendLine(f'OK_LOGOUT {nick}')

    def list(self, channels):
        channels = ' '.join(channels)
        self.sendLine(f'RPL_LIST {channels}')

    def is_on(self, users):
        users = ' '.join(users)
        self.sendLine(f'RPL_ISON {users}')

    def names(self, channel, users):
        users = ' '.join(users)
        self.sendLine(f'RPL_NAMES {channel} {users}')

    def created(self, channel, creator, users):
        users = ' '.join(users)
        self.sendLine(f'OK_CREATED {channel} {creator} {users}')

    def channel_exists(self, channel):
        self.sendLine(f'ERR_EXISTS {channel}')

    def channel_clashed(self, channel):
        self.sendLine(f'ERR_CLASH_CREAT {channel}')

    def channel_deleted(self, channel):
        self.sendLine(f'OK_DELETED {channel}')

    def no_channel(self, channel):
        self.sendLine(f'ERR_NOCHANNEL {channel}')

    def no_perms(self, perm_type, reason):
        self.sendLine(f'ERR_NO_PERM {perm_type} :{reason}')

    def joined(self, channel):
        self.sendLine(f'OK_JOINED {channel}')

    def user_joined(self, channel, user):
        self.sendLine(f'JOINED {channel} {user}')

    def left(self, channel):
        self.sendLine(f'OK_LEFT {channel}')

    def user_left(self, channel, user):
        self.sendLine(f'LEFT {channel} {user}')

    def quit(self, channel):
        self.sendLine(f'OK_QUIT {channel}')

    def user_quit(self, channel, user):
        self.sendLine(f'QUIT {channel} {user}')

    def added(self, channel):
        self.sendLine(f'OK_ADDED {channel}')

    def no_user(self, user):
        self.sendLine(f'ERR_NOUSER {user}')

    def kicked(self, channel, user):
        self.sendLine(f'OK_KICKED {channel} {user}')

    def user_kicked(self, channel, user):
        self.sendLine(f'KICKED {channel} {user}')

    def msg(self, from_user, channel, content):
        self.sendLine(f':{from_user} MSG {channel} :{content}')

    def notify(self, reason, notification):
        self.sendLine(f'NOTIFY {reason} :{notification}')

    # Outgoing messages (server -> server).
    def connect(self, password):
        self.sendLine(f'CONNECT {password}')

    def disconnect(self):
        self.sendLine('DISCONNECT')

    def sync(self):
        self.sendLine('SYNC')


class IRCClient(IRCBase):
    # Outgoing commands.
    def register(self, nick, mail):
        self.sendLine(f'REGISTER {nick} {mail}')

    def login(self, nick):
        self.sendLine(f'LOGIN {nick}')

    def password(self, password):
        self.sendLine(f'PASSWORD {password}')

    def unregister(self):
        self.sendLine('UNREGISTER')

    def logout(self):
        self.sendLine('LOGOUT')

    def list(self):
        self.sendLine('LIST')

    def is_on(self, nicks):
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
    def irc_RPL_PWD(self, _):
        self.password_requested()

    def irc_OK_REG(self, _):
        self.registered()

    def irc_ERR_TAKEN(self, message):
        what = message.params[1]
        if what == 'nick':
            self.nick_taken()
        else:
            self.mail_in_use()

    def irc_ERR_CLASH_REG(self, message):
        what = message.params[1]
        if what == 'nick':
            self.nick_clash()
        else:
            self.mail_clash()

    def irc_OK_UNREG(self, _):
        self.unregistered()

    # Login.
    def irc_OK_LOGIN(self, _):
        self.logged_in()

    def irc_ERR_CLASH_LOGIN(self, _):
        self.login_clash()

    def irc_OK_LOGOUT(self, _):
        self.logged_out()

    # Info.
    def irc_RPL_LIST(self, message):
        channels = message.params
        self.channels_available(channels)

    def irc_RPL_ISON(self, message):
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

    def unregistered(self):
        pass

    # Login.
    def logged_in(self):
        pass

    def login_clash(self):
        pass

    def logged_out(self):
        pass

    # Info.
    def channels_available(self, channels):
        pass

    def users_online(self, users):
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
