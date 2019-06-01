# Partially based on twisted.words.irc
import string
from abc import ABC, abstractmethod

from twisted.protocols import basic
from twisted.python import log


class BadMessage(Exception):
    """Malformed message was encountered."""
    pass


class Message:
    """
    Recognized message sent over the network.

    This class defines what a correct message string looks like - if
    constructor does not raise BadMessage exception, then given
    string is correct.
    """

    whitespace = set(string.whitespace)
    alpha = set(string.ascii_letters) | set('_')

    num_par = {
        'REGISTER': 2,
        'ERR_NUM_PARAMS': 0,
        'OK_REG': 3,
        'ERR_TAKEN': 2,
        'ERR_CLASH_REG': 2,
        'ERR_INTERNAL': 1,

        'RPL_PWD': 0,
        'PASSWORD': 1,

        'UNREGISTER': 0,
        'OK_UNREG': 1,

        'LOGIN': 1,
        'OK_LOGIN': 1,
        'ERR_CLASH_LOGIN': 1,
        'ERR_BAD_PASSWORD': 1,

        'LOGOUT': 0,
        'OK_LOGOUT': 1,

        'LIST': 0,
        'NAMES': 0,
        'HELP': 0,

        'QUIT': 1,

    }

    def __init__(self, string=None, prefix='', command='', params=None):
        params = [] if not params else params
        if string:
            prefix, command, params = self._parse_message(string)

            correct_num_par = self.num_par.get(command, len(params))
            if len(params) != correct_num_par:
                raise BadMessage(f'{command}: bad number of parameters.')

        self.prefix = prefix
        self.command = command.upper()
        self.params = params


    @staticmethod
    def _parse_message(string):
        """
        Perform initial parsing - just splitting into prefix, command
        and parameters, actually.

        :param string:
        :return:
        """
        if not string:
            raise BadMessage('Empty string.')

        prefix, trailing = '', ''
        if string[0] == ':':
            prefix, string = string[1:].split(' ', 1)
        if ':' in string:
            string, trailing = string.split(':', 1)

        if not string or set(string).issubset(Message.whitespace):
            raise BadMessage('No command.')

        args = string.split()
        if trailing:
            args.append(trailing)

        if not set(args[0]).issubset(Message.alpha):
            raise BadMessage('Bad command.')

        return prefix, args[0], args[1:]


class MessageSource:
    """
    A message publisher object.

    Messages come from a remote someone (chat client, server etc.).
    It can register subscribers and notify them upon receiving
    a message.
    """

    def __init__(self):
        self.__subscriber = None

    def register_subscriber(self, subscriber):
        self.__subscriber = subscriber

    def unregister_subscriber(self):
        self.__subscriber = None

    def notify(self, message):
        if self.__subscriber:
            self.__subscriber.handle_message(message)

    def connection_closed(self):
        if self.__subscriber:
            self.__subscriber.on_connection_closed()


class MessageSubscriber(ABC):
    """
    A subscriber to a MessageSource.
    """

    @abstractmethod
    def handle_message(self, message):
        """
        This method is called with correct Messages when they
        appear at MessageSource.
        """

    @abstractmethod
    def on_connection_closed(self):
        """
        This method is called when connection is closed for whatever
        reason.
        """


class BaseProtocol(basic.LineReceiver, MessageSource):
    """
    Physical connection to someone who communicates using Messages.

    On one hand, it is a source of correct messages. But on the other,
    it also provides sendLine method, that sends lines of text to a
    remote someone.
    """

    delimiter = '\n'.encode('utf-8')

    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')

        try:
            message = Message(line)
            self.notify(message)
        except BadMessage as e:
            log.err(f'ERR: {str(e)}')

    def sendLine(self, line):
        line = line.encode('utf-8', errors='ignore')
        super().sendLine(line)

    def loseConnection(self):
        self.transport.loseConnection()

    def connectionLost(self, reason):
        self.connection_closed()


class Endpoint(ABC):
    """
    Facade in front of a BaseProtocol.

    It provides a set of chosen methods that send messages to a remote
    someone.
    """

    def __init__(self, protocol):
        self._protocol = protocol

    def send(self, line):
        self._protocol.sendLine(line)
