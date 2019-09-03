import sqlite3
from functools import wraps
from twisted.python import log, failure
from twisted.internet import defer
from twisted.application import service
from twisted.enterprise import adbapi
from chat import config
from chat.chat_server.db import query


def log_operation(method):
    @defer.inlineCallbacks
    @wraps(method)
    def wrapper(*args, **kwargs):
        try:
            res = yield method(*args, **kwargs)
            log.msg(f'DB: {method.__name__} CALL SUCCESSFUL')
            return res
        except failure.Failure as f:
            log.err(f'DB: {method.__name__} CALL FAILURE: {f.getErrorMessage()}')
            raise f

    return wrapper


# TODO: add timeouts on DB operations!
class DBService(service.Service):
    def __init__(self):
        self._dbpool = None

    def startService(self):
        self._dbpool = adbapi.ConnectionPool(config.db_type,
                                             config.db_name,
                                             check_same_thread=False,
                                             cp_openfun=self._enable_fk)
        self._init_db()

    def stopService(self):
        self._dbpool.close()

    def _init_db(self):
        self._dbpool.runInteraction(self._create_tables)

    @staticmethod
    def _enable_fk(con):
        con.execute('PRAGMA foreign_keys = ON;')

    @staticmethod
    def _create_tables(transaction):
        transaction.execute(query.create_table_user)
        transaction.execute(query.create_table_channel)
        transaction.execute(query.create_table_is_member)
        transaction.execute(query.create_table_notification)

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

    @log_operation
    @defer.inlineCallbacks
    def users_registered(self, nicks):
        select = query.select_nicks(len(nicks))
        result = yield self._dbpool.runQuery(select, nicks)
        return [r[0] for r in result]

    @log_operation
    def add_user(self, nick, mail, password):
        return self._dbpool.runOperation(query.insert_user, (nick, mail, password))

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

    @log_operation
    @defer.inlineCallbacks
    def channel_exists(self, channel_name):
        channels = yield self._dbpool.runQuery(query.select_channel, (channel_name,))
        return len(channels) != 0

    @staticmethod
    def _add_members(transaction, member_tuples):
        transaction.executemany(query.insert_member, member_tuples)

    @log_operation
    @defer.inlineCallbacks
    def add_members(self, channel_name, nicks):
        member_tuples = [(nick, channel_name) for nick in nicks]
        yield self._dbpool.runInteraction(self._add_members, member_tuples)

    @staticmethod
    def _delete_members(transaction, member_tuples):
        transaction.executemany(query.delete_member, member_tuples)

    @log_operation
    @defer.inlineCallbacks
    def delete_members(self, channel_name, nicks):
        member_tuples = [(nick, channel_name) for nick in nicks]
        yield self._dbpool.runInteraction(self._delete_members, member_tuples)

    @log_operation
    @defer.inlineCallbacks
    def add_channel(self, channel_name, creator, public=True, nicks=None):
        yield self._dbpool.runOperation(query.insert_channel, (channel_name, creator, int(public)))

        if nicks and not public:
            self.add_members(channel_name, nicks)

    @log_operation
    def delete_channel(self, channel_name):
        return self._dbpool.runOperation(query.delete_channel, (channel_name,))

    @log_operation
    @defer.inlineCallbacks
    def get_channel_creator(self, channel_name):
        creator = yield self._dbpool.runQuery(query.select_creator, (channel_name,))
        if creator:
            return creator[0][0]
        else:
            return None

    @log_operation
    @defer.inlineCallbacks
    def get_channel_mode(self, channel_name):
        mode = yield self._dbpool.runQuery(query.select_mode, (channel_name,))

        if mode:
            return 'pub' if mode[0][0] == 1 else 'priv'
        else:
            return None

    @log_operation
    @defer.inlineCallbacks
    def is_member(self, nick, channel_name):
        result = yield self._dbpool.runQuery(query.select_is_member, (nick, channel_name))
        return result != []

    @log_operation
    @defer.inlineCallbacks
    def get_pub_channels(self):
        channels = yield self._dbpool.runQuery(query.select_pub_channels)
        return [c[0] for c in channels]

    @log_operation
    @defer.inlineCallbacks
    def get_priv_channels(self, nick=None):
        channels = yield self._dbpool.runQuery(query.select_priv_channels, (nick,))
        return [c[0] for c in channels]

    @log_operation
    def add_notification(self, author, target, notification):
        return self._dbpool.runOperation(query.insert_notification, (author, target, notification))

    @log_operation
    @defer.inlineCallbacks
    def get_notifications(self, user):
        results = yield self._dbpool.runQuery(query.select_notifications, (user,))
        return results

    @log_operation
    def delete_notifications(self, user):
        return self._dbpool.runOperation(query.delete_notifications, (user,))

    @log_operation
    @defer.inlineCallbacks
    def get_members(self, channel):
        results = yield self._dbpool.runQuery(query.select_members, (channel,))
        return [r[0] for r in results]
