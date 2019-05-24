import sqlite3
from sqlite3 import Error
from flask import *


DATABASE = '/home/brtqkr/PycharmProjects/Flask/database'


def create_connection(db):
    try:
        conn = sqlite3.connect(db)
        return conn
    except Error as e:
        print(e)

    return conn


# extracts all messages from records and returns Array
def extract_messages(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM Messages")
    rows = cur.fetchall()

    messages = list()
    for row in rows:
        messages.append(row[0] + ">" + row[1])

    print(messages)
    return messages


# extracts all ratings from records and forms 2D Array, returns 2D Array
def extract_ratings(conn):
    cur = conn.cursor()
    cur.execute("SELECT * FROM Messages")
    rows = cur.fetchall()

    ratings = list()
    for i in range(0, len(rows)):
        stats = list()
        for j in range(2, 8):
            stats.append(rows[i][j])
        ratings.append(stats)
    return ratings


app = Flask(__name__)


# messages: regular Array of messages received from server
@app.route('/', endpoint='load_live', methods=['POST'])
def main_page():
    # nie wiem w jakiej formie będzie przesyłane; data roboczo potem można json czy coś
    messages=request.data
    return render_template("main_page.html",
                           messages=["abc", "def", "ghi", "jkl", "abc", "def", "ghi", "jkl", "abc", "def", "ghi", "jkl",
                                     "abc", "def", "ghi", "jkl", "abc", "def", "ghi", "jkl", "abc", "def", "ghi", "jkl",
                                     "abc", "def", "ghi", "jkl"])


# stats: 2D ARRAY [[toxic, severeToxic, ...], [toxic, severeToxic, ...]]
# messages: regular Array of messages processed from db
@app.route('/history')
def history():
    conn = create_connection(DATABASE)
    messages = extract_messages(conn)
    ratings = extract_ratings(conn)
    return render_template("history.html", stats=ratings, messages=messages)


@app.route('/stats')
def stats():
    return render_template("stats.html")


if __name__ == "__main__":
    app.run(debug=True)
