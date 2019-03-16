# -*- coding: utf-8 -*-



import json

from flask import Flask
from flask import flash, render_template



app = Flask(__name__)
app.secret_key = 'L4mJRdpkjXLEBG6R#L;y@KiX8'



DATA_FILE = 'feeds.json'


@app.route('/')
def home():
    context = {}
    try:
        context['feeds'] = json.load(open(DATA_FILE))

    except FileNotFoundError:
        flash('Data file "{}" not found.'.format(DATA_FILE), 'error')

    return render_template('home.html', **context)

