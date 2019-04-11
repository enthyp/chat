# based on https://github.com/wesdoyle/python-twisted-chat-server/blob/master/chatserver.py
import argparse
import datetime

from twisted.internet import defer
from twisted.internet.protocol import Factory, ClientFactory, connectionDone
from twisted.protocols.basic import LineReceiver

import server.util.colors as colors


class ChatProtocol(LineReceiver):
    def __init__(self):
        self.name = None
        self.state = 'REGISTER'

    def rawDataReceived(self, data):
        print("Raw data received!")
        self.transport.loseConnection()

    def sendLine(self, line):
        super().sendLine(line.encode('utf-8', errors='ignore'))

    def connectionMade(self):
        self.sendLine('Connected to server.')
        self.sendLine(self._get_time())
        self.sendLine('Choose a username:')

    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')
        if self.state == "REGISTER":
            self.handle_register(line)
        else:
            self.handle_msg(line)

    def handle_register(self, name):
        if name in self.factory.users:
            self.sendLine(f'Sorry, {name} is taken. Try something else.')
            return

        self.name = name
        self.factory.users[name] = self
        self.state = 'CHAT'

        welcome_msg = f'Welcome to the server, {name}.\n'
        if len(self.factory.users) > 1:
            participants = ', '.join(self.factory.users)
            welcome_msg += 'Participants: {}'.format(participants)
        else:
            welcome_msg += "You're the only one here."
        self.sendLine(self.mark(welcome_msg, colors.GREEN))

        joined_msg = f'{name} has joined the chanel.'
        self.broadcast_message(self.mark(joined_msg, colors.GREEN))

    @defer.inlineCallbacks
    def handle_msg(self, message):
        message = yield self.factory.check(message)
        message = self._get_time() + f'<{self.name}> {message}'
        self.broadcast_message(message)

    def connectionLost(self, reason=connectionDone):
        left_msg = self.mark(f'{self.name} has left the channel.', colors.BLUE)
        if self.name in self.factory.users:
            del self.factory.users[self.name]
            self.broadcast_message(left_msg)

    def broadcast_message(self, message):
        for name, protocol in self.factory.users.items():
            if protocol != self:
                protocol.sendLine(message)

    @staticmethod
    def _get_time():
        return datetime.datetime.now().strftime('%Y/%m/%d %H:%M:%S')

    @staticmethod
    def mark(msg, color):
        return color + msg + colors.ENDC


class ChatFactory(Factory):
    protocol = ChatProtocol

    def __init__(self, mark, ban, service):
        super().__init__()
        self.mark = mark
        self.ban = ban
        self.service = service
        self.users = {}

    def check(self, line):
        d = defer.Deferred()
        if self.mark:
            pass
        d.callback(line)
        return d


class MLClient(LineReceiver):
    def rawDataReceived(self, data):
        print("Raw data received!")
        self.transport.loseConnection()

    def lineReceived(self, line):
        pass


class MLClientFactory(ClientFactory):
    protocol = MLClient

    def __init__(self, port):
        self.port = port
        self.deferred = defer.Deferred()

    def finished(self, msg):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.callback(msg)

    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.errback(reason)


def parse_args():
    parser = argparse.ArgumentParser(description='Basic server server in Twisted.')
    parser.add_argument('port', type=int, help='Port to listen on.')
    parser.add_argument('service_port', type=int, help='Port on which checking service is available.')
    parser.add_argument('-l', action='store_true', help='Run on localhost (as opposed to all).')
    parser.add_argument('-m', action='store_true', help='Mark toxic messages.')
    parser.add_argument('-b', '--ban', type=int, default=0, help='Max number of toxic messages until ban. ')

    return parser.parse_args()


def server_main(port, service_port, ban, mark, local):
    service = MLClientFactory(service_port)
    factory = ChatFactory(mark, ban, service)

    from twisted.internet import reactor
    reactor.listenTCP(port, factory, interface='localhost' if local else '')

if __name__ == '__main__':
    args = parse_args()
    server_main(args.port, args.service_port, args.ban, args.m, args.l)

    from twisted.internet import reactor
    reactor.run()
