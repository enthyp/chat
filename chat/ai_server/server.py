import typing
import json
from twisted.application import service
from twisted.internet.protocol import ServerFactory
from twisted.protocols.basic import LineReceiver
from twisted.python import log
from twisted.web.client import Agent
from twisted.internet.defer import succeed
from twisted.web.iweb import IBodyProducer
from zope.interface import implementer

from chat import communication as comm
from chat import config
import ai


class ToxicServiceProtocol(LineReceiver):

    delimiter = '\n'.encode('utf-8')

    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')

        try:
            message = comm.Message(line)
            self.factory.on_msg(message)
        except comm.BadMessage as e:
            log.err(f'ERR: {str(e)}')


@implementer(IBodyProducer)
class StringProducer(object):

    def __init__(self, body):
        self.body = body
        self.length = len(body)

    def startProducing(self, consumer):
        consumer.write(self.body)
        return succeed(None)

    def pauseProducing(self):
        pass

    def stopProducing(self):
        pass


class ToxicFactory(ServerFactory):
    protocol = ToxicServiceProtocol

    def __init__(self, service):
        self.service = service

        from twisted.internet import reactor
        self.agent = Agent(reactor)

    def on_msg(self, msg):
        content = msg.params[1]
        scores = self.service.process(content)
        log.msg(f'Got scores: {scores}')

        body_dict = {'author': msg.prefix,
                     'channel': msg.params[0],
                     'content': content,
                     'scores': scores}
        body_json = json.dumps(body_dict, ensure_ascii=False).encode(errors='ignore')

        body = StringProducer(body_json)
        d = self.agent.request('POST'.encode(),
                               config.flask_host.encode(errors='ignore'),
                               bodyProducer=body)

        def on_response(_):
            log.msg('Sent to monitor!')

        def on_failure(reason):
            print(reason)
            log.err('Failed to send to monitor: ' + reason.getErrorMessage())

        d.addCallbacks(on_response, on_failure)


class ToxicService(service.Service):
    def __init__(self, model_path, get_model: typing.Callable[[str], ai.Model]):
        self.model_path = model_path
        self.get_model = get_model
        self.model = None

    def startService(self):
        self.model = self.get_model(self.model_path)
        log.msg(f'Loaded model from {self.model_path}')

        self.factory = ToxicFactory(self)
        from twisted.internet import reactor
        reactor.listenTCP(config.ai_server_port,
                          self.factory,
                          interface=config.ai_server_host)

    def process(self, msg):
        return self.model.process(msg)
