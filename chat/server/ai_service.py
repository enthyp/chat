import typing

from twisted.application import internet, service
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver
from twisted.python import log

import ai


class AIResponse:
    err_msg = 'Provide a colon-separated sequence of numbers.'

    def __init__(self, scores=None):
        if scores:
            if isinstance(scores, str):
                scores = scores.split(':')
            if isinstance(scores, list):
                try:
                    self.scores = list(map(float, scores))
                except ValueError:
                    raise ValueError(self.err_msg)
            else:
                raise ValueError(self.err_msg)
        else:
            self.scores = []

    def __str__(self):
        return ':'.join(map(str, self.scores))

    def __bool__(self):
        return bool(self.scores)

    # Example.
    def positive(self):
        return any([s > 0.5 for s in self.scores])


class ToxicServiceProtocol(LineReceiver):
    def rawDataReceived(self, data):
        log.err('Raw data received!')
        self.transport.loseConnection()

    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')
        log.msg(f'Received line: {line}')

        scores = self.factory.serve(line)
        log.msg(f'Got scores: {scores}')

        self.sendLine(str(AIResponse(scores)))

    def sendLine(self, line):
        super().sendLine(line.encode('utf-8', errors='ignore'))


class ToxicFactory(ServerFactory):
    protocol = ToxicServiceProtocol

    def __init__(self, service):
        self.service = service

    # synchronous method
    def serve(self, line):
        return self.service.process(line)


class ToxicService(service.Service):
    def __init__(self, get_model: typing.Callable[[], ai.Model]):
        self.get_model = get_model
        self.model = None

    def startService(self):
        service.Service.startService(self)
        self.model = self.get_model()
        log.msg(f'Loaded model.')

    def process(self, msg):
        return self.model.process(msg)

# Service setup.
service_port = 10001
iface = 'localhost'


def get_model_dummy(_):
    return ai.MockChecker()


def get_model_legit():
    checker = ai.Checker()
    checker.load_from_package(100)
    return checker

supervisor = service.MultiService()
toxic_service = ToxicService(get_model_legit)
toxic_service.setServiceParent(supervisor)

factory = ToxicFactory(toxic_service)
tcp_service = internet.TCPServer(service_port, factory, interface=iface)
tcp_service.setServiceParent(supervisor)

application = service.Application('toxic_service')
supervisor.setServiceParent(application)
