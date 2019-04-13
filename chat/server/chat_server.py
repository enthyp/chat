import argparse
import datetime

from twisted.python import failure
from twisted.internet import defer
from twisted.internet.protocol import Factory, ClientFactory, connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.protocols.policies import TimeoutMixin

import util.colors as colors


class ParseError(Exception):
    pass


def parse_args():
    parser = argparse.ArgumentParser(description='Basic server server in Twisted.')
    parser.add_argument('port', type=int, help='Port to listen on.')
    parser.add_argument('service_port', type=int, help='Port on which checking service is available.')
    parser.add_argument('-l', action='store_true', help='Run on localhost (as opposed to all).')
    parser.add_argument('-b', '--ban', type=int, default=None, help='Max number of toxic messages until ban.')

    args = parser.parse_args()
    if args.ban and args.ban < 0:
        raise ParseError("ban should be non-negative.")

    return args


class ChatProtocol(LineReceiver):

    REGISTER = 0
    CHAT = 1

    def __init__(self, warnings):
        self.name = None
        self.warnings = warnings + 1
        self.state = self.REGISTER

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
        if self.state == self.REGISTER:
            self.handle_register(line)
        else:
            self.handle_msg(line)

    def handle_register(self, name):
        if name in self.factory.users:
            self.sendLine(f'Sorry, {name} is taken. Try something else.')
            return

        self.name = name
        self.factory.users[name] = self
        self.state = self.CHAT

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
        if self.factory.ban:
            scores = ''
            try:
                scores = yield self.factory.get_scores(message, 1)
            except failure.Failure:
                print('Failed to get scores from ML service.')

            if scores:
                scores = scores.split(':')
            else:
                scores = []
            self.handle_scores(message, scores)
        else:
            message = self._get_time() + f'<{self.name}> {message}'
            self.broadcast_message(message)

    def handle_scores(self, message, scores):
        if not scores or all([m < 0.5 for m in map(float, scores)]):
            message = self._get_time() + f'<{self.name}> {message}'
            self.broadcast_message(message)
        else:
            self.warnings -= 1
            if self.warnings > 1:
                self.sendLine(self.mark('Consider yourself warned. Shame, shame.', colors.RED))
            elif self.warnings == 1:
                self.sendLine(self.mark("One more and you're out.", colors.RED))
            elif self.name in self.factory.users:
                del self.factory.users[self.name]
                left_msg = self.mark(f'{self.name} was kicked out.', colors.RED)
                self.broadcast_message(left_msg)
                self.transport.loseConnection()

    def connectionLost(self, reason=connectionDone):
        if self.name in self.factory.users:
            del self.factory.users[self.name]
            left_msg = self.mark(f'{self.name} has left the channel.', colors.BLUE)
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

    def __init__(self, ban, service_port):
        super().__init__()
        self.users = {}
        self.ban = ban is not None
        self.warnings = ban
        self.service_port = service_port

    def buildProtocol(self, addr):
        protocol = self.protocol(self.warnings)
        protocol.factory = self
        return protocol

    def get_scores(self, line, timeout):
        factory = MLClientFactory(self.service_port, line, timeout)
        from twisted.internet import reactor
        reactor.connectTCP('localhost', self.service_port, factory)  # TODO: add host choice.

        return factory.deferred


class MLClient(LineReceiver, TimeoutMixin):
    def timeoutConnection(self):
        print('Service timeout.')
        self.transport.abortConnection()
        self.factory.got_scores('')

    def rawDataReceived(self, data):
        print("Raw data received!")
        self.transport.loseConnection()

    def connectionMade(self):
        self.setTimeout(self.factory.timeout)
        self.sendLine(self.factory.line)

    def sendLine(self, line):
        super().sendLine(line.encode('utf-8', errors='ignore'))

    # TODO: make a superclass that handles bytes properly!
    def lineReceived(self, line):
        self.setTimeout(None)
        line = line.decode('utf-8', errors='ignore')
        self.factory.got_scores(line)


class MLClientFactory(ClientFactory):
    protocol = MLClient

    def __init__(self, port, line, timeout):
        self.port = port
        self.line = line
        self.timeout = timeout
        self.deferred = defer.Deferred()

    def got_scores(self, msg):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.callback(msg)

    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.errback(reason)


def server_main(port, service_port, ban, local):
    factory = ChatFactory(ban, service_port)

    from twisted.internet import reactor
    reactor.listenTCP(port, factory, interface='localhost' if local else '')

if __name__ == '__main__':
    try:
        args = parse_args()
        server_main(args.port, args.service_port, args.ban, args.l)

        from twisted.internet import reactor
        reactor.run()
    except ParseError as e:
        print(e)
