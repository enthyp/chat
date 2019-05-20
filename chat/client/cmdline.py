import os
from twisted.protocols import basic
from twisted.internet import stdio


class IOProtocol(basic.LineReceiver):
    delimiter = os.linesep.encode('utf-8')

    def __init__(self, parent):
        self.parent = parent

    def lineReceived(self, line):
        line = line.decode('utf-8', errors='ignore')
        self.parent.handle_line(line)

    def sendLine(self, line):
        line = line.encode('utf-8', errors='ignore')
        super().sendLine(line)


class CMDLine:
    def __init__(self):
        self.io = stdio.StandardIO(IOProtocol(self))
        self.client = None

    def register_client(self, client):
        self.client = client

    def handle_line(self, line):
        if self.client:
            self.client.handle_input(line)

    def send(self, line):
        self.io.protocol.sendLine(line)
