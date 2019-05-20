import argparse
from twisted.internet.protocol import ClientFactory
from twisted.internet import defer
from twisted.python import log

from chat import communication as comm
from chat.client import cmdline


class Command:
    def __init__(self, command, content):
        self.command = command
        self.content = content


class ServerEndpoint(comm.Endpoint):
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

    def names(self):
        self.send(f'NAMES')

    def msg(self, channel, content):
        self.send(f'MSG {channel} :{content}')

    def help(self):
        self.send('HELP')


class State(comm.MessageSubscriber):
    def __init__(self, protocol, endpoint, iface, manager):
        self.endpoint = endpoint
        self.iface = iface
        self.manager = manager

        protocol.register_subscriber(self)
        iface.register_client(self.manager)

    def on_connection_closed(self):
        self.connected = False
        self.manager.on_connection_closed()

    def handle_message(self, message):
        method_name = f'msg_{message.command}'
        method = getattr(self, method_name, None)

        if method is None:
            self.msg_unknown(message)
        else:
            method(message)

    def msg_unknown(self, message):
        cmd = message.command
        params = message.params
        self.iface.send(f'Unexpected server message {cmd} with params: {params}', color='RED')

    def handle_input(self, line):
        raise NotImplementedError


class InitialState(State):

    opening_line = 'Type "login", "register" or "quit".'

    def __init__(self, protocol, endpoint, iface, manager):
        super().__init__(protocol, endpoint, iface, manager)
        self.iface.send(self.opening_line, color='BLUE')

    def handle_input(self, line):
        if line == 'login':
            self.manager.state_logging_in()
        elif line == 'register':
            self.manager.state_registering()
        elif line == 'quit':
            self.manager.close_connection()
        else:
            self.iface.send(self.opening_line, color='BLUE')


class RegisteringState(State):

    login_line = 'LOGIN: '
    mail_line = 'EMAIL: '
    password_line = 'PASSWORD: '
    wait_line = 'Awaiting server response...'
    registered_line = 'Registered!'

    def __init__(self, protocol, endpoint, iface, manager):
        super().__init__(protocol, endpoint, iface, manager)

        self.iface.send(self.login_line, color='YELLOW')
        self.reg_deferred = defer.Deferred()
        self.reg_deferred.addCallback(self._login_callback)

    def _login_callback(self, login):
        self.iface.send(self.mail_line, color='YELLOW')
        self.reg_deferred = defer.Deferred()
        self.reg_deferred.addCallback(lambda m: self.endpoint.register(login, m))

    def handle_input(self, line):
        if self.reg_deferred:
            self.reg_deferred, d = None, self.reg_deferred
            d.callback(line)
        else:
            self.iface.send(self.wait_line, color='YELLOW')

    def msg_RPL_PWD(self, _):
        self.iface.send(self.password_line, color='YELLOW')
        self.reg_deferred = defer.Deferred()
        self.reg_deferred.addCallback(lambda l: self.endpoint.password(l))

    def msg_OK_REG(self, _):
        self.iface.send(self.registered_line, color='YELLOW')

    def msg_OK_LOGIN(self, _):
        self.manager.state_logged_in()

    def msg_ERR_INTERNAL(self, message):
        communicate = message.params[0]
        self.iface.send(communicate, color='RED')

        self.iface.send(self.login_line, color='YELLOW')
        self.reg_deferred = defer.Deferred()
        self.reg_deferred.addCallback(self._login_callback)

    def msg_ERR_TAKEN(self, message):
        what = message.params[0]
        if what == 'nick':
            self.iface.send('Nick already in use!', color='RED')
        else:
            self.iface.send('E-mail already in use!', color='RED')

        self.iface.send(self.login_line, color='YELLOW')
        self.reg_deferred = defer.Deferred()
        self.reg_deferred.addCallback(self._login_callback)


class LoggingInState(State):

    login_line = 'LOGIN: '
    password_line = 'PASSWORD: '
    wait_line = 'Awaiting server response...'

    def __init__(self, protocol, endpoint, iface, manager):
        super().__init__(protocol, endpoint, iface, manager)

        self.iface.send(self.login_line, color='YELLOW')
        self.login_deferred = defer.Deferred()
        self.login_deferred.addCallback(lambda l: self.endpoint.login(l))

    def handle_input(self, line):
        if self.login_deferred:
            self.login_deferred, d = None, self.login_deferred
            d.callback(line)
        else:
            self.iface.send(self.wait_line, color='YELLOW')

    def msg_RPL_PWD(self, _):
        self.iface.send(self.password_line, color='YELLOW')
        self.login_deferred = defer.Deferred()
        self.login_deferred.addCallback(lambda l: self.endpoint.password(l))

    def msg_OK_LOGIN(self, _):
        self.manager.state_logged_in()

    def msg_ERR_INTERNAL(self, message):
        communicate = message.params[0]
        self.iface.send(communicate, color='RED')

        self.iface.send(self.login_line, color='YELLOW')
        self.reg_deferred = defer.Deferred()
        self.login_deferred.addCallback(lambda l: self.endpoint.login(l))

    def msg_ERR_BAD_PASSWORD(self, message):
        count = message.params[0]
        self.iface.send(f'Password incorrect! Trials to go: {count}', color='RED')

        self.iface.send(self.password_line, color='YELLOW')
        self.login_deferred = defer.Deferred()
        self.login_deferred.addCallback(lambda l: self.endpoint.password(l))

    def msg_ERR_NOUSER(self, _):
        self.iface.send('No such user registered!', color='RED')
        self.manager.state_init(again=True)

    def msg_CLOSED(self, message):
        communicate = message.params[0]
        self.iface.send(f'Server closed connection! Reason: {communicate}', color='RED')
        self.manager.state_init(again=True)


class LoggedInState(State):

    welcome_line = 'Welcome to the chat.'

    def __init__(self, protocol, endpoint, iface, manager, starting=True):
        super().__init__(protocol, endpoint, iface, manager)

        if starting:
            self.iface.send(self.welcome_line, color='BLUE')

    def handle_input(self, line):
        try:
            cmd = comm.Message(line)
            self.handle_command(cmd)
        except comm.BadMessage as e:
            self.iface.send(str(e), color='RED')

    def handle_command(self, cmd):
        method_name = f'cmd_{cmd.command}'
        method = getattr(self, method_name, None)

        if method is None:
            self.cmd_unknown(cmd)
        else:
            method(cmd)

    def cmd_unknown(self, cmd):
        self.iface.send(f'Unexpected command: {cmd}', color='RED')

    def cmd_HELP(self, _):
        self.endpoint.help()

    def msg_RPL_HELP(self, message):
        content = message.params[0]
        self.iface.send(content, color='YELLOW')

    def cmd_UNREGISTER(self, _):
        self.endpoint.unregister()

    def msg_OK_UNREG(self, _):
        self.iface.send('You were unregistered.', color='YELLOW')
        self.manager.state_init(again=True)

    def cmd_LOGOUT(self, _):
        self.endpoint.logout()

    def msg_OK_LOGOUT(self, _):
        self.iface.send('You were logged out.', color='YELLOW')
        self.manager.state_init(again=True)

    def cmd_LIST(self, _):
        self.endpoint.list()

    def msg_RPL_LIST(self, message):
        channels = message.params
        content = ', '.join(channels[1:])

        if channels[0] == 'priv':
            content = 'Private channels: ' + content
        else:
            content = 'Public channels: ' + content

        self.iface.send(content, color='YELLOW')

    def cmd_ISON(self, cmd):
        nicks = cmd.params
        self.endpoint.is_on(nicks)

    def msg_RPL_ISON(self, message):
        nicks = ', '.join(message.params)
        self.iface.send('Users online: ' + nicks, color='YELLOW')

    def cmd_CREATE(self, cmd):
        try:
            channel, mode, *nicks = cmd.params
            self.endpoint.create(channel, nicks, mode == 'priv')
        except ValueError:
            self.iface.send('Not enough parameters for CREATE command!', color='RED')

    def msg_OK_CREATED(self, message):
        channel, _, _, *users = message.params
        if users:
            users = ', '.join(users)
            self.iface.send(f'Channel {channel} created with users: {users}', color='YELLOW')
        else:
            self.iface.send(f'Channel {channel} created.', color='YELLOW')

    def msg_ERR_EXISTS(self, message):
        channel = message.params[0]
        self.iface.send(f'Channel {channel} already exists!', color='RED')

    def msg_ERR_BAD_NAME(self, _):
        self.iface.send('Incorrect channel name (must start with a "#")!', color='RED')

    def msg_ERR_BAD_MODE(self, _):
        self.iface.send('Incorrect channel mode (either "priv" or "pub")!', color='RED')

    def cmd_DELETE(self, cmd):
        try:
            channel = cmd.params[0]
            self.endpoint.delete(channel)
        except IndexError:
            self.iface.send('Pass channel name.', color='RED')

    def msg_OK_DELETED(self, message):
        channel = message.params[0]
        self.iface.send(f'Channel {channel} deleted.', color='YELLOW')

    def msg_ERR_NO_PERM(self, message):
        perm_type, reason = message.params
        self.iface.send(f'You have no {perm_type} permission: {reason}', color='RED')

    def msg_ERR_NOCHANNEL(self, message):
        channel = message.params[0]
        self.iface.send(f'Channel {channel} does not exist!', color='RED')

    def cmd_JOIN(self, cmd):
        try:
            channel = cmd.params[0]
            self.endpoint.join(channel)
        except IndexError:
            self.iface.send('Pass channel name.', color='RED')

    def msg_OK_JOINED(self, message):
        channel, _ = message.params
        self.manager.state_conversation(channel)

    def cmd_QUIT(self, cmd):
        pass


class ConversationState(State):

    joined_line = 'You join the channel.'

    def __init__(self, protocol, endpoint, iface, manager, channel):
        super().__init__(protocol, endpoint, iface, manager)
        self.channel = channel
        self.iface.send(self.joined_line, color='YELLOW')

    def handle_input(self, line):
        cmd = self._parse_line(line)

        if not cmd.command:
            self.cmd_MSG(cmd)
        else:
            method_name = f'cmd_{cmd.command}'
            method = getattr(self, method_name, None)

            if method is None:
                self.cmd_unknown(cmd)
            else:
                method(cmd)

    @staticmethod
    def _parse_line(line):
        line = line.strip()
        cmd = ''

        if line[0] == '/':
            try:
                cmd, line = line.split(maxsplit=1)
            except ValueError:
                cmd = line[1:]
                line = ''

        return Command(cmd.upper(), line)

    def cmd_unknown(self, cmd):
        self.iface.send(f'Unexpected command: {cmd.command}', color='RED')

    def cmd_LEAVE(self, _):
        self.endpoint.leave(self.channel)

    def msg_OK_LEFT(self, message):
        channel, _ = message.params
        self.iface.send(f'You left channel {channel}.', color='YELLOW')
        self.manager.state_logged_in(starting=False)

    def cmd_MSG(self, cmd):
        self.endpoint.msg(self.channel, cmd.content)

    def msg_MSG(self, message):
        author = message.prefix
        _, content = message.params
        self.iface.send(content, prefix=f'>>> {author}: ')

    def msg_OK_DELETED(self, _):
        self.manager.state_logged_in(starting=False)

    def cmd_NAMES(self, _):
        self.endpoint.names()

    def msg_RPL_NAMES(self, message):
        channel, *nicks = message.params
        nicks = ', '.join(nicks)
        self.iface.send(f'Users on {channel} channel: {nicks}', color='YELLOW')


class ConnectionFactory(ClientFactory):

    protocol = comm.BaseProtocol

    def __init__(self, parent):
        super().__init__()
        self.parent = parent

    def buildProtocol(self, addr):
        protocol = self.protocol()
        self.parent.endpoint = ServerEndpoint(protocol)
        self.parent.protocol = protocol
        self.parent.state_init()

        return protocol

    def clientConnectionFailed(self, connector, reason):
        log.err('Failed to connect: ' + reason.getErrorMessage())


class Client:
    def __init__(self, host, port, iface):
        self.host = host
        self.port = port
        self.iface = iface
        self.factory = ConnectionFactory(self)
        self.protocol = None
        self.endpoint = None
        self.state = None

    def _connect(self):
        from twisted.internet import reactor
        reactor.connectTCP(self.host, self.port, self.factory)

    def run(self):
        from twisted.internet import reactor
        self._connect()
        reactor.run()

    def handle_input(self, line):
        self.state.handle_input(line)

    def on_connection_closed(self):
        pass

    def close_connection(self):
        self.protocol.loseConnection()
        self.iface.lose_connection()

        from twisted.internet import reactor
        reactor.stop()

    def state_init(self, again=False):
        if again:
            self._connect()
        else:
            self.state = InitialState(self.protocol, self.endpoint, self.iface, self)

    def state_logging_in(self):
        self.state = LoggingInState(self.protocol, self.endpoint, self.iface, self)

    def state_registering(self):
        self.state = RegisteringState(self.protocol, self.endpoint, self.iface, self)

    def state_logged_in(self, starting=True):
        self.state = LoggedInState(self.protocol, self.endpoint, self.iface, self, starting)

    def state_conversation(self, channel):
        self.state = ConversationState(self.protocol, self.endpoint, self.iface, self, channel)


def parse_args():
    parser = argparse.ArgumentParser(description='Basic chat client in Twisted.')
    parser.add_argument('port', type=int, help='Port to connect to.')
    parser.add_argument('host', nargs='?', default='localhost', help='Host to connect to.')

    return parser.parse_args()


def client_main():
    args = parse_args()
    iface = cmdline.CMDLine()   # will depend on args
    client = Client(args.host, args.port, iface=iface)
    iface.register_client(client)

    client.run()

if __name__ == '__main__':
    client_main()
