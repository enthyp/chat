import os
from twisted.python import log
from twisted.application import internet, service
from twisted.internet import defer, error
from twisted.internet.protocol import Factory, ClientFactory, connectionDone
from twisted.protocols.basic import LineReceiver
from twisted.protocols.policies import TimeoutMixin

import chat.server.util as util
from chat.server.ai_service import AIResponse


class ChatProtocol(LineReceiver):

    REGISTER = 0
    CHAT = 1

    def __init__(self, warnings):
        self.name = None
        self.warnings = warnings + 1
        self.state = self.REGISTER

    def rawDataReceived(self, data):
        log.err('Raw data received!')
        self.transport.loseConnection()

    def sendLine(self, line):
        super().sendLine(line.encode('utf-8', errors='ignore'))

    def connectionMade(self):
        log.msg('User connected.')
        self.sendLine('Connected to server.')
        self.sendLine(util.get_time())
        self.sendLine('Choose a username:')

    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')
        if self.state == self.REGISTER:
            self.handle_register(line)
        else:
            self.handle_msg(line)

    def handle_register(self, name):
        if name in self.factory.users:
            log.msg(f'Registration failure: {name}')
            self.sendLine(f'Sorry, {name} is taken. Try something else.')
            return

        log.msg(f'Registration successful: {name}')
        self.name = name
        self.factory.users[name] = self
        self.state = self.CHAT

        welcome_msg = f'Welcome to the server, {name}.\n'
        if len(self.factory.users) > 1:
            participants = ', '.join(self.factory.users)
            welcome_msg += 'Participants: {}'.format(participants)
        else:
            welcome_msg += "You're the only one here."
        self.sendLine(util.mark(welcome_msg, 'GREEN'))

        joined_msg = f'{name} has joined the chanel.'
        self.broadcast_message(util.mark(joined_msg, 'GREEN'))

    @defer.inlineCallbacks
    def handle_msg(self, message):
        log.msg(f'Message received: {message}')
        if self.factory.ban:
            scores = ''
            try:
                log.msg(f'Getting scores for {message}')
                scores = yield self.factory.get_scores(message, 1)
                log.msg('Got scores.')
            except error.ConnectError:
                log.err('Failed to get scores from toxic_service.')

            response = AIResponse(scores)
            self.handle_ai_response(message, response)
        else:
            log.msg('Broadcasting.')
            message = util.get_time() + f'<{self.name}> {message}'
            self.broadcast_message(message)

    def handle_ai_response(self, message, response):
        if response.positive():
            log.msg('Message scored positive.')
            self.warnings -= 1
            if self.warnings > 1:
                self.sendLine(util.mark('Consider yourself warned. Shame on you.', 'RED'))
            elif self.warnings == 1:
                self.sendLine(util.mark("One more and you're out.", 'RED'))
            elif self.name in self.factory.users:
                del self.factory.users[self.name]
                left_msg = util.mark(f'{self.name} was kicked out.', 'RED')
                self.broadcast_message(left_msg)
                self.transport.loseConnection()
        else:
            if response:
                log.msg('Message scored negative.')
            log.msg('Broadcasting.')
            message = util.get_time() + f'<{self.name}> {message}'
            self.broadcast_message(message)

    def connectionLost(self, reason=connectionDone):
        log.msg(f'Connection lost for {self.name}')
        if self.name in self.factory.users:
            del self.factory.users[self.name]
            left_msg = util.mark(f'{self.name} has left the channel.', 'BLUE')
            self.broadcast_message(left_msg)

    def broadcast_message(self, message):
        for name, protocol in self.factory.users.items():
            if protocol != self:
                protocol.sendLine(message)


class ChatFactory(Factory):
    protocol = ChatProtocol

    def __init__(self, ban, service_port):
        super().__init__()
        self.conversations = []
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
        log.err('Service timeout.')
        self.transport.abortConnection()
        self.factory.got_scores('')

    def rawDataReceived(self, data):
        log.err('Raw data received!')
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

# Service setup.
# chat_port = int(os.environ.get('PORT', 8080))  # for Heroku
chat_port = 8080
service_port = 10001
iface = 'localhost'
ban = 3

factory = ChatFactory(ban, service_port)
tcp_service = internet.TCPServer(chat_port, factory, interface=iface)

application = service.Application('chat_service')
tcp_service.setServiceParent(application)
