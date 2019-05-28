import sqlite3
from sqlite3 import Error
from flask import *
import json


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
<<<<<<< HEAD
        messages.append(row[0] + "> " + row[2])
=======
        messages.append(row[0] + ">" + row[1])
>>>>>>> d6a0124e4db3fd97e7464548454d64b3e19f0e05

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
<<<<<<< HEAD
        for j in range(3, 9):
=======
        for j in range(2, 8):
>>>>>>> d6a0124e4db3fd97e7464548454d64b3e19f0e05
            stats.append(rows[i][j])
        ratings.append(stats)
    return ratings


app = Flask(__name__)


<<<<<<< HEAD
@app.route('/') # , endpoint='load_live', methods=['POST'])
def main_page():
    live_list = list("")
    b = 0

=======
@app.route('/', endpoint='load_live', methods=['POST'])
def main_page():
>>>>>>> d6a0124e4db3fd97e7464548454d64b3e19f0e05
    data = json.loads(request.data)
    author = data['author']
    channel_name = data['channel']
    message = data['content']
    scores = data['scores']
<<<<<<< HEAD

    # exemplary params to write into db
    # author = "User"
    # message = "Fuck"
    # channel_name = "Channel2"
    # scores = [1, 2, 1, 1, 1, 1]
    # print(author, channel_name, message, scores)

    # saving last 40 messages into live list
    live_list.append(author + "> " + message)
    if b > 39:
        live_list = live_list[1:41]
    else:
        b += 1

    conn = create_connection(DATABASE)
    cur = conn.cursor()
    params = (author, channel_name, message, scores[0], scores[1], scores[2], scores[3], scores[4], scores[5])
    cur.execute("INSERT INTO Messages VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)", params)
    conn.commit()

    return render_template("main_page.html", messages=live_list)
=======
    print(author, channel_name, message, scores)

    return render_template("main_page.html",
                           messages=["abc", "def", "ghi", "jkl", "abc", "def", "ghi", "jkl", "abc", "def", "ghi", "jkl",
                                     "abc", "def", "ghi", "jkl", "abc", "def", "ghi", "jkl", "abc", "def", "ghi", "jkl",
                                     "abc", "def", "ghi", "jkl"])
>>>>>>> d6a0124e4db3fd97e7464548454d64b3e19f0e05


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
