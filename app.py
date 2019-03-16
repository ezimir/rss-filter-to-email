# -*- coding: utf-8 -*-



import json
import os

from flask import Flask, request
from flask import flash, render_template, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import validators
from wtforms.fields.html5 import URLField



app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', '')

csrf = CSRFProtect(app)
csrf.init_app(app)



DATA_FILE = 'feeds.json'


@app.route('/')
def home():
    context = {}
    try:
        context['feeds'] = json.load(open(DATA_FILE))

    except FileNotFoundError:
        flash('Data file "{}" not found.'.format(DATA_FILE), 'error')

    return render_template('home.html', **context)


class AddFeedForm(FlaskForm):
    url = URLField('URL', [
        validators.DataRequired(),
        validators.URL(),
    ])

@app.route('/add-feed', methods = ['GET', 'POST'])
def add_feed():
    form = AddFeedForm(request.form)
    if request.method == 'POST' and form.validate():
        with open(DATA_FILE, 'a+') as f:
            try:
                feeds = json.load(f)
            except json.decoder.JSONDecodeError:
                feeds = []
            feeds.append({
                'url': form.data['url'],
            })
            json.dump(feeds, f, indent = 4)
        flash('Feed saved!')
        return redirect(url_for('home'))
    return render_template('add_feed.html', form = form)

