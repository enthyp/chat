from flask import request, render_template, g
import json

from monitor import app, db

live_list = []
channels_list = []


# extracts all messages from records and returns a list
def extract_messages(rows):
    return [r[0] + "> " + r[2] for r in rows]


# extracts all ratings from records and returns list of tuples
def extract_ratings(rows):
    return [list(row[3:]) for row in rows]


# extracts all channels from records and returns list
def extract_channels(rows):
    return list({row[1] for row in rows})


@app.route('/', methods=['GET', 'POST'])
def main_page():
    global channels_list
    global live_list

    if request.method == 'POST':
        data = json.loads(request.data)
        author = data['author']
        channel_name = data['channel']
        message = data['content']
        scores = data['scores']

        params = (author, channel_name, message, *scores[:6])
        conn = db.get_db()
        conn.execute('INSERT INTO message VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)', params)
        conn.commit()

        live_list.append(author + "> " + message)

        if len(live_list) == 40:
            live_list = live_list[1:]

        return '', 204
    else:
        conn = db.get_db()
        cur = conn.cursor()
        cur.execute('SELECT * FROM message')
        rows = cur.fetchall()

        channels_list = extract_channels(rows)
        channels_list = [name[1:] for name in channels_list]
        return render_template("main_page.html", messages=live_list, channels=channels_list)


# stats: 2D ARRAY [[toxic, severeToxic, ...], [toxic, severeToxic, ...]]
# messages: regular Array of messages processed from db
@app.route('/history')
def history():
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM message')
    rows = cur.fetchall()

    messages = extract_messages(rows)
    ratings_list = extract_ratings(rows)
    channels_list = extract_channels(rows)

    for i in range(len(ratings_list)):
        for j in range(6):

            if ratings_list[i][j] < 0.5:
                ratings_list[i][j] = 0
            elif ratings_list[i][j] < 0.65:
                ratings_list[i][j] = 1
            elif ratings_list[i][j] < 0.80:
                ratings_list[i][j] = 2
            else:
                ratings_list[i][j] = 3

    return render_template("history.html", stats=ratings_list, messages=messages, channels=channels_list)


@app.route('/channel/<name>')
def channel(name):
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM message WHERE channel = ?', ('#' + name,))
    rows = cur.fetchall()

    messages = extract_messages(rows)
    ratings_list = extract_ratings(rows)
    channels_list = [name]

    for i in range(len(ratings_list)):
        for j in range(6):

            if ratings_list[i][j] < 0.5:
                ratings_list[i][j] = 0
            elif ratings_list[i][j] < 0.65:
                ratings_list[i][j] = 1
            elif ratings_list[i][j] < 0.80:
                ratings_list[i][j] = 2
            else:
                ratings_list[i][j] = 3

    return render_template("channel.html", stats=ratings_list, messages=messages, channels=channels_list, name=name)
