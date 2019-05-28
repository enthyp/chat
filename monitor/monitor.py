from flask import request, render_template, g
import json

from monitor import app, db

live_list = []


# extracts all messages from records and returns a list
def extract_messages(rows):
    return [r[0] + "> " + r[2] for r in rows]


# extracts all ratings from records and returns list of tuples
def extract_ratings(rows):
    return [row[3:] for row in rows]


@app.route('/', methods=['GET', 'POST'])
def main_page():
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

        global live_list
        live_list.append(author + "> " + message)

        if len(live_list) == 40:
            live_list = live_list[1:]

        return '', 204
    else:
        return render_template("main_page.html", messages=live_list)


# stats: 2D ARRAY [[toxic, severeToxic, ...], [toxic, severeToxic, ...]]
# messages: regular Array of messages processed from db
@app.route('/history')
def history():
    conn = db.get_db()
    cur = conn.cursor()
    cur.execute('SELECT * FROM message')
    rows = cur.fetchall()

    messages = extract_messages(rows)
    ratings = extract_ratings(rows)
    return render_template("history.html", stats=ratings, messages=messages)


@app.route('/stats')
def stats():
    return render_template("stats.html")