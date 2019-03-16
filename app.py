# -*- coding: utf-8 -*-



import json

from flask import Flask, request
from flask import flash, render_template, redirect, url_for
from wtforms import Form, validators
from wtforms.fields.html5 import URLField



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


class AddFeedForm(Form):
    url = URLField('URL', [validators.DataRequired()])

@app.route('/add-feed', methods = ['GET', 'POST'])
def add_feed():
    form = AddFeedForm(request.form)
    if request.method == 'POST' and form.validate():
        flash('Saved')
        return redirect(url_for('home'))
    return render_template('add_feed.html', form = form)

