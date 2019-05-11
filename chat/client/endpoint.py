from chat.communication import Endpoint


class ServerEndpoint(Endpoint):
    def register(self, user, mail):  # ok
        self.send(f'REGISTER {user} {mail}')

    def login(self, user):  # ok
        self.send(f'LOGIN {user}')

    def password(self, password):  # ok
        self.send(f'PASSWORD {password}')

    def unregister(self):  # ok
        self.send('UNREGISTER')

    def logout(self):  # ok
        self.send('LOGOUT')

    def list(self):  # ok
        self.send('LIST')

    def is_on(self, nicks):  # ok
        nick_list = ' '.join(nicks)
        self.send(f'ISON {nick_list}')

    def create(self, channel, nicks, private=False):
        nick_list = ' '.join(nicks)
        mode = 'priv' if private else 'pub'
        self.send(f'CREATE {channel} {mode} {nick_list}')

    def delete(self, channel):
        self.send(f'DELETE {channel}')

    def join(self, channel):
        self.send(f'JOIN {channel}')

    def leave(self, channel):
        self.send(f'LEAVE {channel}')

    def quit(self, channels):
        channel_list = ' '.join(channels)
        self.send(f'QUIT {channel_list}')

    def add(self, channel, nicks):
        nick_list = ' '.join(nicks)
        self.send(f'ADD {channel} {nick_list}')

    def invite(self, channel, nicks):
        nick_list = ' '.join(nicks)
        self.send(f'INVITE {channel} {nick_list}')

    def kick(self, channel, nicks):
        nick_list = ' '.join(nicks)
        self.send(f'KICK {channel} {nick_list}')

    def names(self, channel):
        self.send(f'NAMES {channel}')

    def msg(self, channel, content):
        self.send(f'MSG {channel} :{content}')

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
