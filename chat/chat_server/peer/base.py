from twisted.python import log

import chat.communication as comm


class Peer:

    def __init__(self, db, dispatcher, protocol, endpoint):
        self.db = db
        self.dispatcher = dispatcher
        self.protocol = protocol
        self.endpoint = endpoint
        self.state = None

    def lose_connection(self):
        self.protocol.unregister_subscriber()
        self.protocol.loseConnection()
        # TODO: unregister myself from Dispatcher!

    def on_connection_closed(self):
        self.protocol.unregister_subscriber()


class State(comm.MessageSubscriber):

    def __init__(self, protocol, endpoint, manager):
        protocol.register_subscriber(self)
        self.endpoint = endpoint
        self.manager = manager
        self.connected = True
        self.log_msg('starting...')

    def on_connection_closed(self):
        self.connected = False
        self.manager.on_connection_closed()
        self.log_msg('connection closed')

    def handle_message(self, message):
        method_name = f'msg_{message.command}'
        method = getattr(self, method_name, None)

        if method is None:
            self.msg_unknown(message)
        else:
            try:
                method(message)
            except ValueError:
                self.log_err('wrong number of params')

    def msg_unknown(self, message):
        cmd = message.command
        params = message.params
        self.log_err(f'received {cmd} with params: {params}')

    def log_msg(self, communicate):
        name = self.__class__.__name__
        log.msg(f'{name} INFO: {communicate}')

    def log_err(self, communicate):
        name = self.__class__.__name__
        log.err(f'{name} ERR: {communicate}')
