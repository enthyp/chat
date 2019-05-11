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

    alpha = string.ascii_letters
    alphanum = string.ascii_letters + string.digits
    special_chars = '-_[]\`^{}'

    def __init__(self, string):
        prefix, command, params = self._parse_message(string)
        self._validate_message(prefix, command, params)
        self.prefix = prefix
        self.command = command
        self.params = params

    def __str__(self):  # TODO: necessary?
        string = ' '.join([self.command] + self.params)
        if self.prefix:
            string = f':{self.prefix} {string}'

        return string

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

        if not set(string).issubset(Message.alphanum + Message.special_chars):
            raise BadMessage('Bad characters.')

        prefix, trailing = '', ''
        if string[0] == ':':
            prefix, string = string[1:].split(' ', 1)
        if ':' in string:
            string, trailing = string.split(':', 1)

        if not string:
            raise BadMessage('No command.')

        args = string.split()
        if trailing:
            args.append(trailing)

        if prefix and not set(prefix).issubset(Message.alphanum + Message.special_chars):
            raise BadMessage('Bad prefix.')

        if not set(args[0]).issubset(Message.alpha):
            raise BadMessage('Bad command.')

        return prefix, args[0], args[1:]

    def _validate_message(self, prefix, command, params):
        """
        Check if message is correct given its type (the command).

        Most often it amounts to checking if appropriate number
        of parameters were passed etc. This job is delegated to
        methods with names starting with '_validate_'.
        :param prefix:
        :param command:
        :param params:
        :return:
        """
        method_name = f'_validate_{command}'

        try:
            method = getattr(self, method_name)
            return method(prefix, params)
        except AttributeError:
            raise BadMessage(f'Unknown message type: {command}')

    # TODO: finish validation.
    def _validate_OK_REG(self, message):
        pass


class MessageSource(ABC):
    """
    A message publisher object.

    Messages come from a remote someone (chat client, server etc.).
    It can register subscribers and notify them upon receiving
    a message.
    """

    def __init__(self):
        self.__subscribers = set()

    def register_subscriber(self, subscriber):
        self.__subscribers.add(subscriber)

    def unregister_subscriber(self, subscriber):
        self.__subscribers.remove(subscriber)

    def unregister_all(self):
        self.__subscribers = set()

    def notify(self, message):
        for sub in self.__subscribers:
            sub.handle_message(message)


class MessageSubscriber(ABC):
    """
    A subscriber to a MessageSource.

    It's 'handle_message' method is called with beautifully correct
    Messages. All an implementation should do is implement methods
    named 'msg_COMMAND', e.g. msg_OK_REG, that take a Message as an
    argument and do whatever they want with them.
    """

    def __init__(self, source):
        source.register_subscriber(self)

    @abstractmethod
    def handle_message(self, message):
        pass


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
        self.unregister_all()


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

    # def irc_REGISTER(self, message):  # ok
    #     user, mail = message.params
    #     self.register_user(user, mail)
    #
    # def irc_OK_REG(self, message):
    #     user, mail, password = message.params
    #     self.on_user_registered(user, mail, password)
    #
    # def irc_ERR_CLASH_REG(self, message):  # ok
    #     what, value = message.params
    #     if what in ('nick', 'mail'):
    #         self.on_reg_clashed(what, value)
    #     else:
    #         log.err(f'ERR: ERR_CLASH_REG message with incorrect reason: {what}')
    #
    # def irc_OK_UNREG(self, message):  # ok
    #     user = message.params[0]
    #     self.on_user_unregistered(user)
    #
    # def irc_LOGIN(self, message):  # ok
    #     user = message.params[0]
    #     self.login_user(user)
    #
    # def irc_OK_LOGIN(self, message):  # ok
    #     user = message.params[0]
    #     self.on_user_logged_in(user)
    #
    # def irc_ERR_CLASH_LOGIN(self, message):  # ok
    #     user = message.params[0]
    #     self.on_login_clashed(user)
    #
    # def irc_PASSWORD(self, message):  # ok
    #     password = message.params[0]
    #     self.password_received(password)
    #
    # def irc_UNREGISTER(self, _):  # ok
    #     self.unregister_user()
    #
    # def irc_LOGOUT(self, _):  # ok
    #     self.logout_user()
    #
    # def irc_OK_LOGOUT(self, message):  # ok
    #     user = message.params[0]
    #     self.on_user_logged_out(user)
    #
    # def irc_LIST(self, _):  # ok
    #     self.get_channel_list()
    #
    # def irc_ISON(self, message):  # ok
    #     users = message.params
    #     self.get_users_status(users)
    #
    # def irc_CREATE(self, message):
    #     channel, mode = message.params[:2]
    #     if mode in ('priv', 'pub'):
    #         users = message.params[2:]
    #         self.create_channel(channel, mode == 'priv', users)
    #     else:
    #         log.err(f'ERR: CREATE message with incorrect mode: {mode}')
    #
    # def irc_OK_CREATED(self, message):
    #     channel, creator = message.params[:2]
    #     users = message.params[2:]
    #     self.on_channel_created(channel, creator, users)
    #
    # def irc_ERR_CLASH_CREAT(self, message):
    #     channel = message.params[0]
    #     self.on_creation_clashed(channel)
    #
    # def irc_DELETE(self, message):
    #     channel = message.params[0]
    #     self.delete_channel(channel)
    #
    # def irc_OK_DELETED(self, message):
    #     channel = message.params[0]
    #     self.on_channel_deleted(channel)
    #
    # def irc_JOIN(self, message):
    #     channel = message.params[0]
    #     self.join_channel(channel)
    #
    # def irc_JOINED(self, message):
    #     channel, user = message.params
    #     self.on_user_joined(channel, user)
    #
    # def irc_LEAVE(self, message):
    #     channel = message.params[0]
    #     self.leave_channel(channel)
    #
    # def irc_LEFT(self, message):
    #     channel, user = message.params
    #     self.on_user_left(channel, user)
    #
    # def irc_QUIT(self, message):
    #     channel = message.params[0]
    #     self.quit_channel(channel)
    #
    # def irc_USER_QUIT(self, message):
    #     channel, user = message.params
    #     self.on_user_quit(channel, user)
    #
    # def irc_ADD(self, message):
    #     channel = message.params[0]
    #     users = message.params[1:]
    #     self.add_to_channel(channel, users)
    #
    # def irc_ADDED(self, message):
    #     channel = message.params[0]
    #     users = message.params[1:]
    #     self.on_users_added(channel, users)
    #
    # def irc_KICK(self, message):
    #     channel = message.params[0]
    #     users = message.params[1:]
    #     self.kick_from_channel(channel, users)
    #
    # def irc_KICKED(self, message):
    #     channel = message.params[0]
    #     users = message.params[1:]
    #     self.on_users_kicked(channel, users)
    #
    # def irc_NAMES(self, message):
    #     channel = message.params[0]
    #     self.get_users_on_channel(channel)
    #
    # def irc_MSG(self, message):
    #     from_user = message.prefix
    #     channel = message.params[0]
    #     content = message.params[1]
    #     self.message_received(from_user, channel, content)
    #
    # def irc_CONNECT(self, message):
    #     password = message.params[0]
    #     self.server_connected(password)
    #
    # def irc_DISCONNECT(self, _):
    #     self.server_disconnected()
    #
    # def irc_SYNC(self, _):
    #     self.sync_requested()
