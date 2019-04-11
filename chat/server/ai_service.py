import argparse

from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver

import server.util.colors as colors
import server.ai as ai


class ToxicServiceProtocol(LineReceiver):
    def rawDataReceived(self, data):
        print("Raw data received!")
        self.transport.loseConnection()

    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')
        # Synchronous.
        mark = self.factory.check(line)
        self.sendLine(self.make_response(line, mark))

    @staticmethod
    def make_response(line, mark):
        if mark:
            line = colors.RED + line + colors.ENDC
        return line

    def sendLine(self, line):
        super().sendLine(line.encode('utf-8', errors='ignore'))


class ToxicServiceFactory(ServerFactory):
    protocol = ToxicServiceProtocol

    def __init__(self, service):
        self.service = service

    def check(self, line):
        return self.service.check(line)


def parse_args():
    parser = argparse.ArgumentParser(description='Basic server server in Twisted.')
    parser.add_argument('port', type=int, help='Port to listen on.')
    parser.add_argument('-l', action='store_true', help='Run on localhost (as opposed to all).')

    return parser.parse_args()


def service_main(port, local):
    service = ai.Checker()
    factory = ToxicServiceFactory(service)

    from twisted.internet import reactor
    reactor.listenTCP(port, factory, interface='localhost' if local else '')

if __name__ == '__main__':
    args = parse_args()
    service_main(args.port, args.local)

    from twisted.internet import reactor
    reactor.run()

