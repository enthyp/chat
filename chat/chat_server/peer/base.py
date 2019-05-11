from abc import ABC
from twisted.python import log

import chat.communication as comm


class Peer(ABC):

    def __init__(self, db, dispatcher, protocol, endpoint):
        self.db = db
        self.dispatcher = dispatcher
        self.protocol = protocol
        self.endpoint = endpoint
        self.state = None

    def lose_connection(self):
        # TODO: must remove Peer entirely.
        self.protocol.lose_connection()

    def __del__(self):
        # TODO: for now.
        log.msg('Peer taken out with trash.')


class State(ABC, comm.MessageSubscriber):

    def __init__(self, protocol, endpoint, manager):
        super().__init__(protocol)
        self.endpoint = endpoint
        self.manager = manager

    def handle_message(self, message):
        method_name = f'msg_{message.command}'
        method = getattr(self, method_name, None)

        if method is None:
            self.msg_unknown(message)
        else:
            method(message)

    def msg_unknown(self, message):
        self.manager.lose_connection()
        cmd = message.command
        params = message.params
        self.log_err(f'received {cmd} with params: {params}')

    def log_msg(self, communicate):
        name = self.__name__
        log.msg(f'{name} INFO: {communicate}')

    def log_err(self, communicate):
        name = self.__name__
        log.err(f'{name} ERR: {communicate}')
