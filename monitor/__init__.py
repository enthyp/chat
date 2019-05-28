import os
from flask import Flask


app = Flask(__name__)

app.config.update(dict(
    DATABASE=os.path.join(app.root_path, 'flask.db'),
))

import monitor.monitor
