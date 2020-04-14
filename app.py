# -*- coding: utf-8 -*-


import os

from pathlib import Path

from flask import Flask, request
from flask import flash, render_template, redirect, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import validators
from wtforms.fields import StringField
from wtforms.fields.html5 import URLField

from feed import Feeds


app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "")

csrf = CSRFProtect(app)
csrf.init_app(app)

app.config["DEBUG_TB_PROFILER_ENABLED"] = True
toolbar = DebugToolbarExtension(app)
toolbar.init_app(app)


DATA_FILE = "feeds.json"


@app.route("/")
def home():
    context = {}
    try:
        context["feeds"] = Feeds(DATA_FILE)

    except FileNotFoundError:
        flash('Data file "{}" not found.'.format(DATA_FILE), "error")

    return render_template("home.html", **context)


class AddFeedForm(FlaskForm):
    url = URLField("URL", [validators.DataRequired(), validators.URL()])


@app.route("/add-feed", methods=["GET", "POST"])
def add():
    context = {}
    context["form"] = form = AddFeedForm(request.form)
    if request.method == "POST" and form.validate():
        path = Path(DATA_FILE)
        if not path.exists():
            path.touch()
        feeds = Feeds(DATA_FILE)
        feeds.add(form.data["url"])
        flash("Feed saved!")
        return redirect(url_for("home"))
    return render_template("add.html", **context)


class EditFeedForm(FlaskForm):
    url = URLField("URL", [validators.DataRequired(), validators.URL()])
    title = StringField("Title", [validators.DataRequired()])
    filter = StringField("Filter", [validators.Optional()])


@app.route("/feed/<feed_id>", methods=["GET", "POST"])
def feed(feed_id):
    context = {}
    feeds = Feeds(DATA_FILE)
    context["feed"] = feed = feeds.get(feed_id)

    if feed is None:
        return redirect(url_for("home"))

    context["form"] = form = EditFeedForm(request.form)
    if request.method == "POST" and form.validate():
        if request.form["action"] == "delete":
            feeds.delete(feed)
            flash("Feed deleted!")
            return redirect(url_for("home"))
        feed.update(form.data)
        feeds.update(feed)
        return redirect(url_for("feed", feed_id=feed_id))

    for field in form:
        if hasattr(feed, field.name):
            field.process_data(getattr(feed, field.name))

    return render_template("feed.html", **context)
