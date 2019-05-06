import sqlite3
from twisted.python import log, failure
from twisted.internet import defer
from twisted.application import service
from twisted.enterprise import adbapi
from chat.chat_server import config
from chat.chat_server.db import query


def log_operation(method):
    def wrapper(*args, **kwargs):
        try:
            yield method(*args, **kwargs)
            log.msg(f'DB: {method.__name__} CALL SUCCESSFUL')
        except failure.Failure as f:
            log.err(f'DB: {method.__name__} CALL FAILURE: {f.getErrorMessage()}')
            raise f

    return wrapper


class DBService(service.Service):
    def __init__(self):
        self._dbpool = None

    def startService(self):
        self._dbpool = adbapi.ConnectionPool(config.db_type, config.db_name, check_same_thread=False)
        self._init_db()

    def stopService(self):
        self._dbpool.close()

    def _init_db(self):
        self._dbpool.runInteraction(self._create_tables)

    @staticmethod
    def _create_tables(transaction):
        transaction.execute(query.create_table_user)
        transaction.execute(query.create_table_channel)
        transaction.execute(query.create_table_is_member)

    @defer.inlineCallbacks
    def account_available(self, nick, mail):
        try:
            nicks = yield self._dbpool.runQuery(query.select_nick, (nick,))
            mails = yield self._dbpool.runQuery(query.select_mail, (mail,))
            log.msg('DB: account_available CALL SUCCESSFUL')
            return nicks == [], mails == []
        except failure.Failure as f:
            log.err(f'DB: account_available CALL FAILURE: {f.getErrorMessage()}')
            raise

    @defer.inlineCallbacks
    def user_registered(self, nick):
        try:
            nicks = yield self._dbpool.runQuery(query.select_nick, (nick,))
            log.msg('DB: user_registered CALL SUCCESSFUL')
            return nicks != []
        except failure.Failure as f:
            log.err(f'DB: user_registered CALL FAILURE: {f.getErrorMessage()}')
            raise

    @defer.inlineCallbacks
    @log_operation
    def add_user(self, nick, mail, password):
        return self._dbpool.runOperation(query.insert_user, (nick, mail, password))

    @defer.inlineCallbacks
    @log_operation
    def delete_user(self, nick):
        return self._dbpool.runOperation(query.delete_user, (nick,))

    @defer.inlineCallbacks
    def password_correct(self, nick, password):
        try:
            correct_password = yield self._dbpool.runQuery(query.select_password, (nick,))
            log.err('DB: password_correct CALL SUCCESSFUL')
            if correct_password:
                return correct_password[0][0] == password
            else:
                log.err('DB: password_correct CALL FAILURE: no such user in database')
                raise failure.Failure(sqlite3.IntegrityError())
        except failure.Failure as f:
            log.err(f'DB: password_correct FAILURE: {f.getErrorMessage()}')
            raise
