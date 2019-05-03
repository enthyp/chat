import peewee
from chat.chat_server import config

db = peewee.SqliteDatabase(config.db_name)


class BaseModel(peewee.Model):
    class Meta:
        database = db


class User(BaseModel):
    nick = peewee.TextField(unique=True)
    mail = peewee.TextField(unique=True)
    password = peewee.TextField()


class Channel(BaseModel):
    name = peewee.TextField(unique=True)
    creator = peewee.ForeignKeyField(User, backref='created')
    public = peewee.BooleanField()


class IsMember(BaseModel):
    user = peewee.ForeignKeyField(User, 'channels')
    channel = peewee.ForeignKeyField(Channel, 'members')

    class Meta:
        indexes = (
            (('user', 'channel'), True),
        )


class Database:
    def __init__(self):
        self._create_tables()

    @staticmethod
    def _create_tables():
        with db:
            db.create_tables([User, Channel, IsMember])
