# -*- coding: utf-8 -*-



import feedparser
import json
import os
import uuid
from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup
from flask import Flask, request
from flask import flash, render_template, redirect, url_for
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import validators
from wtforms.fields import StringField
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
                'original': title,
            })
            f.truncate(0)
            json.dump({'feeds': feeds}, f, indent = 4)

        flash('Feed saved!')
        return redirect(url_for('home'))
    return render_template('add_feed.html', form = form)


class FeedForm(FlaskForm):
    url = URLField('URL', [
        validators.DataRequired(),
        validators.URL(),
    ])
    title = StringField('Title', [
        validators.DataRequired(),
    ])
    filter = StringField('Filter', [
        validators.Optional(),
    ])


@app.route('/feed/<feed_id>', methods = ['GET', 'POST'])
def show_feed(feed_id):
    data = json.load(open(DATA_FILE))
    feed = list(filter(lambda feed: feed['id'] == feed_id, data['feeds']))[0]

    attrs = ['url', 'title', 'filter']
    form = FeedForm(request.form)
    if request.method == 'POST' and form.validate():
        updated = {key: val for key, val in form.data.items() if key in attrs}
        feed.update(updated)

        with open(DATA_FILE, 'w+') as f:
            f.truncate(0)
            json.dump(data, f, indent = 4)

        flash('Feed saved!')
        return redirect(url_for('home'))

    for attr in attrs:
        field = getattr(form, attr)
        field.process_data(feed.get(attr))

    return render_template('show_feed.html', feed = feed, form = form)


@app.route('/feed/<feed_id>/preview')
def preview_feed(feed_id):
    data = json.load(open(DATA_FILE))
    feed = list(filter(lambda feed: feed['id'] == feed_id, data['feeds']))[0]
    domain = "{url.scheme}://{url.netloc}".format(url = urlparse(feed['url']))

    data = feedparser.parse(feed['url'])
    feed['entries'] = data['entries']
    if feed.get('filter'):
        feed['entries'] = filter(lambda entry: feed['filter'] in entry['title'], feed['entries'])
    for entry in feed['entries']:
        # clear HTML from summary
        soup = BeautifulSoup(entry['summary'], 'html.parser')
        entry['summary'] = soup.text

        # fix images
        for content in entry['content']:
            soup = BeautifulSoup(content['value'], 'html.parser')
            images = soup.find_all("img")
            for image in images:
                # ensure max width
                image['style'] = 'max-width: 100%'
                # ensure full src path
                if image['src'].startswith('/'):
                    image['src'] = urljoin(domain, image['src'])
            content['value'] = soup.prettify()
    return render_template('preview_feed.html', feed = feed)


