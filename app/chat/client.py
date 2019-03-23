from twisted.internet import reactor, protocol, stdio
from twisted.protocols import basic 
import os

port = 8000

class LineReceiver3(basic.LineReceiver):
    def sendLine(self, line):
        super().sendLine(line)

class ServerClient(LineReceiver3):
    def connectionMade(self):
        self.factory.stdio = self    

    def lineReceived(self, line):
       self.factory.out(line) 

class ServerClientFactory(protocol.ClientFactory):
    protocol = ServerClient

    def __init__(self, callback):
        self.callback = callback
        self.stdio = None

    def out(self, line):
        self.callback(line)

class ChatClient(LineReceiver3):
    delimiter = os.linesep.encode()
    def connectionMade(self):
        self.tcpfactory = ServerClientFactory(self.sendLine)
        self.connector = reactor.connectTCP('localhost', 8000, self.tcpfactory)

    def lineReceived(self, line):
        self.tcpfactory.stdio.sendLine(line)


stdio.StandardIO(ChatClient())
print("Chat cliented connected to server on port %s" % (port, ))
reactor.run()

