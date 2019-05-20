import argparse
from twisted.internet.protocol import ClientFactory
from twisted.internet import defer
from twisted.python import log

from chat import communication as comm
from chat.client import cmdline
from chat import util


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
        msg = util.mark(f'Unexpected server message {cmd} with params: {params}', 'RED')
        self.iface.send(msg)

    def handle_input(self, line):
        raise NotImplementedError


class InitialState(State):

    opening_line = util.mark('Type "login" or "register".', 'BLUE')

    def __init__(self, protocol, endpoint, iface, manager):
        super().__init__(protocol, endpoint, iface, manager)
        self.iface.send(self.opening_line)

    def handle_input(self, line):
        if line == 'login':
            self.manager.state_logging_in()
        elif line == 'register':
            self.manager.state_registering()
        else:
            self.iface.send(self.opening_line)


class RegisteringState(State):

    login_line = 'LOGIN: '
    mail_line = 'EMAIL: '
    password_line = 'PASSWORD: '
    wait_line = 'Awaiting server response...'
    registered_line = 'Registered!'

    def __init__(self, protocol, endpoint, iface, manager):
        super().__init__(protocol, endpoint, iface, manager)

        self.iface.send(self.login_line)
        self.reg_deferred = defer.Deferred()
        self.reg_deferred.addCallback(self._login_callback)

    def _login_callback(self, login):
        self.iface.send(self.mail_line)
        self.reg_deferred = defer.Deferred()
        self.reg_deferred.addCallback(lambda m: self.endpoint.register(login, m))

    def handle_input(self, line):
        if self.reg_deferred:
            self.reg_deferred, d = None, self.reg_deferred
            d.callback(line)
        else:
            self.iface.send(self.wait_line)

    def msg_RPL_PWD(self, _):
        self.iface.send(self.password_line)
        self.reg_deferred = defer.Deferred()
        self.reg_deferred.addCallback(lambda l: self.endpoint.password(l))

    def msg_OK_REG(self, _):
        self.iface.send(self.registered_line)

    def msg_OK_LOGIN(self, _):
        self.manager.state_logged_in()

    def msg_ERR_INTERNAL(self, message):
        pass

    def msg_ERR_TAKEN(self, message):
        pass


class LoggingInState(State):

    login_line = 'LOGIN: '
    password_line = 'PASSWORD: '
    wait_line = 'Awaiting server response...'

    def __init__(self, protocol, endpoint, iface, manager):
        super().__init__(protocol, endpoint, iface, manager)

        self.iface.send(self.login_line)
        self.login_deferred = defer.Deferred()
        self.login_deferred.addCallback(lambda l: self.endpoint.login(l))

    def handle_input(self, line):
        if self.login_deferred:
            self.login_deferred, d = None, self.login_deferred
            d.callback(line)
        else:
            self.iface.send(self.wait_line)

    def msg_RPL_PWD(self, _):
        self.iface.send(self.password_line)
        self.login_deferred = defer.Deferred()
        self.login_deferred.addCallback(lambda l: self.endpoint.password(l))

    def msg_OK_LOGIN(self, _):
        self.manager.state_logged_in()

    def msg_ERR_INTERNAL(self, message):
        pass

    def msg_ERR_BAD_PASSWORD(self, message):
        pass

    def msg_ERR_NOUSER(self, message):
        pass


class LoggedInState(State):

    welcome_line = util.mark('Welcome to the chat.', 'BLUE')

    def __init__(self, protocol, endpoint, iface, manager):
        super().__init__(protocol, endpoint, iface, manager)

        self.iface.send(self.welcome_line)

    def handle_input(self, line):
        try:
            cmd = comm.Message(line)
            self.handle_command(cmd)
        except comm.BadMessage as e:
            msg = util.mark(str(e), 'RED')
            self.iface.send(msg)

    def handle_command(self, cmd):
        method_name = f'cmd_{cmd.command}'
        method = getattr(self, method_name, None)

        if method is None:
            self.cmd_unknown(cmd)
        else:
            try:
                method(cmd)
            except ValueError:
                msg = util.mark(f'Wrong number of params', 'RED')
                self.iface.send(msg)

    def cmd_unknown(self, cmd):
        msg = util.mark(f'Unexpected command: {cmd}', 'RED')
        self.iface.send(msg)

    def cmd_HELP(self, _):
        self.endpoint.help()

    def msg_RPL_HELP(self, message):
        content = message.params[0]
        self.iface.send(content)

    def cmd_LIST(self, _):
        self.endpoint.list()

    def msg_RPL_LIST(self, message):
        channels = message.params
        content = ', '.join(channels)
        self.iface.send(content)


class ConversationState(State):

    def __init__(self, protocol, endpoint, iface, manager):
        super().__init__(protocol, endpoint, iface, manager)

    @staticmethod
    def _parse_line(line):
        line = line.strip()
        cmd = ''

        if line[0] == '/':
            cmd, line = line.split(max=1)

        return Command(cmd.upper(), line)


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

    clientConnectionLost = clientConnectionFailed


class Client:
    def __init__(self, host, port, iface):
        self.host = host
        self.port = port
        self.iface = iface
        self.factory = ConnectionFactory(self)
        self.protocol = None
        self.endpoint = None
        self.state = None

    def run(self):
        from twisted.internet import reactor
        reactor.connectTCP(self.host, self.port, self.factory)
        reactor.run()

    def handle_input(self, line):
        self.state.handle_input(line)

    def on_connection_closed(self):
        pass

    def state_init(self):
        self.state = InitialState(self.protocol, self.endpoint, self.iface, self)

    def state_logging_in(self):
        self.state = LoggingInState(self.protocol, self.endpoint, self.iface, self)

    def state_registering(self):
        self.state = RegisteringState(self.protocol, self.endpoint, self.iface, self)

    def state_logged_in(self):
        self.state = LoggedInState(self.protocol, self.endpoint, self.iface, self)

    def state_conversation(self):
        self.state = ConversationState(self.protocol, self.endpoint, self.iface, self)


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
