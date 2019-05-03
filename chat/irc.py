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
    # Outgoing messages.
    def 


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
        what = message.params[0]
        if what == 'nick':
            self.nick_taken()
        else:
            self.mail_in_use()

    def irc_ERR_CLASH_REG(self, message):
        what = message.params[0]
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
        users = message.params[1:]
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
        pass

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
        content = message.params[-1]
        self.got_message(from_user, content)

    def irc_NOTIFY(self, message):
        # TODO: different notification types (reasons)?
        reason = message.params[0]
        notification = message.params[-1]
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
    def got_message(self, from_user, content):
        pass

    def notified(self, reason, notification):
        pass
