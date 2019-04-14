import argparse
from twisted.internet.protocol import ClientFactory, connectionDone
from twisted.internet import stdio
from twisted.python import log
from twisted.protocols.basic import LineReceiver
import os


class IOProtocol(LineReceiver):
    delimiter = os.linesep.encode('utf-8')

    def __init__(self, parent):
        self.parent = parent

    def rawDataReceived(self, data):
        print("Raw data received!")
        self.transport.loseConnection()

    def lineReceived(self, line):
        self.parent.sendLine(line)

    def sendLine(self, line):
        super().sendLine(line)


class ChatClientProtocol(LineReceiver):
    def __init__(self):
        super().__init__()
        self.io = stdio.StandardIO(IOProtocol(self))

    def rawDataReceived(self, data):
        print("Raw data received!")
        self.transport.loseConnection()

    def sendLine(self, line):
        super().sendLine(line)

    def lineReceived(self, line):
        self.io.protocol.sendLine(line)

    def connectionLost(self, reason=connectionDone):
        print('Connection to server closed.')


class ChatClientFactory(ClientFactory):
    protocol = ChatClientProtocol

    def clientConnectionFailed(self, connector, reason):
        log.err('Failed to connect: ' + reason.getErrorMessage())

    clientConnectionLost = clientConnectionFailed


def parse_args():
    parser = argparse.ArgumentParser(description='Basic server server in Twisted.')
    parser.add_argument('port', type=int, help='Port to connect to.')
    parser.add_argument('host', nargs='?', default='localhost', help='Host to connect to.')

    return parser.parse_args()


def client_main():
    args = parse_args()

    factory = ChatClientFactory()

    from twisted.internet import reactor
    reactor.connectTCP(args.host, args.port, factory)
    reactor.run()

if __name__ == '__main__':
    client_main()
