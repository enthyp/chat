from twisted.protocols import basic
from twisted.python import log


class IRCBadMessage(Exception):
    """Incorrect message format."""
    pass


class IRCMessage:
    def __init__(self, string):
        prefix, command, params = self._parse_msg(string)
        self.prefix = prefix
        self.command = command
        self.params = params

    @staticmethod
    def _parse_msg(string):
        if not string:
            raise IRCBadMessage('Empty string.')

        prefix, trailing = '', ''
        if string[0] == ':':
            prefix, string = string[1:].split(' ', 1)
        if ':' in string:
            string, trailing = string.split(':', 1)

        if not string:
            raise IRCBadMessage('No command.')

        args = string.split()
        if trailing:
            args.append(trailing)

        return prefix, args[0], args[1:]

    def __str__(self):  # TODO: necessary?
        string = ' '.join([self.command] + self.params)
        if self.prefix:
            string = f':{self.prefix} {string}'

        return string


class IRC(basic.LineReceiver):
    def handle_command(self, command):
        pass

    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')
        self.handle_command(line)

    def sendLine(self, line):
        line = line.encode('utf-8', errors='ignore')
        super().sendLine(line)


class IRCClient(basic.LineReceiver):
    def register(self, nick, mail):
        self.sendLine(f'REGISTER {nick} {mail}')

    def login(self, nick):
        self.sendLine(f'LOGIN {nick}')

    def password(self, password):
        self.sendLine(f'PASSWORD {password}')

    def handle_message(self, message):
        pass

    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')
        self.handle_command(line)

    def sendLine(self, line):
        line = line.encode('utf-8', errors='ignore')
        super().sendLine(line)
