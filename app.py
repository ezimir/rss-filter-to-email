# -*- coding: utf-8 -*-



import feedparser
import json
import os
import uuid

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
        context.update(json.load(open(DATA_FILE)))

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
        feeds = []
        if os.path.exists(DATA_FILE):
            try:
                feeds = json.load(open(DATA_FILE))['feeds']

            except json.decoder.JSONDecodeError:
                pass

        with open(DATA_FILE, 'w+') as f:
            response = feedparser.parse(form.data['url'])
            title = response.get('feed', {}).get('title', '')
            feeds.append({
                'id': str(uuid.uuid4()),
                'url': form.data['url'],
                'title': title,
            })
            f.truncate(0)
            json.dump({'feeds': feeds}, f, indent = 4)

        flash('Feed saved!')
        return redirect(url_for('home'))
    return render_template('add_feed.html', form = form)

@app.route('/feed/<feed_id>')
def show_feed(feed_id):
    feeds = json.load(open(DATA_FILE))['feeds']
    feed = list(filter(lambda feed: feed['id'] == feed_id, feeds))[0]
    data = feedparser.parse(feed['url'])
    feed['entries'] = data['entries']
    return render_template('show_feed.html', feed = feed)

