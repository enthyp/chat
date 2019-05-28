import sqlite3
from flask import g

from monitor import app


def connect_db():
    """Connects to the specific database."""
    conn = sqlite3.connect(app.config['DATABASE'])
    return conn


def init_db():
    """Initializes the database."""
    db = get_db()
    db.cursor().execute('CREATE TABLE IF NOT EXISTS message ('
                        'author TEXT NOT NULL,'
                        'channel TEXT NOT NULL,'
                        'content TEXT NOT NULL,'
                        'score1 REAL NOT NULL,'
                        'score2 REAL NOT NULL,'
                        'score3 REAL NOT NULL,'
                        'score4 REAL NOT NULL,'
                        'score5 REAL NOT NULL,'
                        'score6 REAL NOT NULL);')
    db.commit()


@app.cli.command('initdb')
def initdb_command():
    """Creates the database tables."""
    init_db()
    print('Initialized the database.')


def get_db():
    """Opens a new database connection if there is none yet for the
    current application context.
    """
    if not hasattr(g, 'sqlite_db'):
        g.sqlite_db = connect_db()
    return g.sqlite_db


@app.teardown_appcontext
def close_db(error):
    """Closes the database again at the end of the request."""
    if hasattr(g, 'sqlite_db'):
        g.sqlite_db.close()
