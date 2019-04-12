import argparse
import datetime

from twisted.python import failure
from twisted.internet import defer
from twisted.internet.protocol import Factory, ClientFactory, connectionDone
from twisted.protocols.basic import LineReceiver

import server.util.colors as colors

# TODO: use the same protocol for MLClient as at MLService (based at LineReceiver)
# so they can be used to send message and receive response on handle_msg. 

# TODO: have a separate method (for callback) at ChatProtocol to deal with the result
# from MLService. Maybe think how to better separate these concepts? Every f'in thing
# is being handled in ChatProtocol o.O


def parse_args():
    parser = argparse.ArgumentParser(description='Basic server server in Twisted.')
    parser.add_argument('port', type=int, help='Port to listen on.')
    parser.add_argument('service_port', type=int, help='Port on which checking service is available.')
    parser.add_argument('-l', action='store_true', help='Run on localhost (as opposed to all).')
    parser.add_argument('-m', action='store_true', help='Mark toxic messages.')
    parser.add_argument('-b', '--ban', type=int, default=0, help='Max number of toxic messages until ban. ')

    return parser.parse_args()


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
        scores = ''
        try:
            scores = yield self.factory.get_scores(message)
        except failure.Failure:
            print('Failed to get scores from ML service.')

        if scores:
            scores = scores.split(':')
        else:
            scores = []

        self.handle_scores(message, scores)

    def handle_scores(self, message, scores):
        if not scores or all([m < 0.5 for m in map(float, scores)]):
            message = self._get_time() + f'<{self.name}> {message}'
            self.broadcast_message(message)
        else:
            self.sendLine('Consider yourself warned. Shame, shame.')

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

    def __init__(self, mark, ban, service_port):
        super().__init__()
        self.users = {}
        self.mark = mark
        self.ban = ban
        self.service_port = service_port

    def get_scores(self, line):
        if not self.mark:
            return defer.succeed('')

        factory = MLClientFactory(self.service_port, line)
        from twisted.internet import reactor
        reactor.connectTCP('localhost', self.service_port, factory)  # TODO: add host choice.

        return factory.deferred


class MLClient(LineReceiver):
    def rawDataReceived(self, data):
        print("Raw data received!")
        self.transport.loseConnection()

    def connectionMade(self):
        self.sendLine(self.factory.line)

    def sendLine(self, line):
        super().sendLine(line.encode('utf-8', errors='ignore'))

    # TODO: make a superclass that handles them bytes properly!
    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')
        self.transport.loseConnection()  # ?
        self.factory.got_scores(line)


class MLClientFactory(ClientFactory):
    protocol = MLClient

    def __init__(self, port, line):
        self.port = port
        self.line = line
        self.deferred = defer.Deferred()

    def got_scores(self, msg):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.callback(msg)

    def clientConnectionFailed(self, connector, reason):
        if self.deferred is not None:
            d, self.deferred = self.deferred, None
            d.errback(reason)


def server_main(port, service_port, ban, mark, local):
    factory = ChatFactory(mark, ban, service_port)

    from twisted.internet import reactor
    reactor.listenTCP(port, factory, interface='localhost' if local else '')

if __name__ == '__main__':
    args = parse_args()
    server_main(args.port, args.service_port, args.ban, args.m, args.l)

    from twisted.internet import reactor
    reactor.run()
