# -*- coding: utf-8 -*-


import feedparser
import json
import os
import uuid

from flask import Flask, request
from flask import flash, render_template, redirect, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import validators
from wtforms.fields import StringField
from wtforms.fields.html5 import URLField

from feed import Feeds
from entries import Feed


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
def add_feed():
    form = AddFeedForm(request.form)
    if request.method == "POST" and form.validate():
        feeds = []
        if os.path.exists(DATA_FILE):
            try:
                feeds = json.load(open(DATA_FILE))["feeds"]

            except json.decoder.JSONDecodeError:
                pass

        with open(DATA_FILE, "w+") as f:
            response = feedparser.parse(form.data["url"])
            title = response.get("feed", {}).get("title", "")
            feeds.append(
                {
                    "id": str(uuid.uuid4()),
                    "url": form.data["url"],
                    "title": title,
                    "original": title,
                }
            )
            f.truncate(0)
            json.dump({"feeds": feeds}, f, indent=4)

        flash("Feed saved!")
        return redirect(url_for("home"))
    return render_template("add_feed.html", form=form)


class FeedForm(FlaskForm):
    url = URLField("URL", [validators.DataRequired(), validators.URL()])
    title = StringField("Title", [validators.DataRequired()])
    filter = StringField("Filter", [validators.Optional()])


@app.route("/feed/<feed_id>", methods=["GET", "POST"])
def feed(feed_id):
    context = {}
    feeds = Feeds(DATA_FILE)
    context["feed"] = feed = feeds.get(feed_id)

    context["form"] = form = FeedForm(request.form)
    if request.method == "POST" and form.validate():
        feeds.update(feed_id, form.data)
        flash("Feed saved!")

    for field in form:
        if hasattr(feed, field.name):
            field.process_data(getattr(feed, field.name))
    return render_template("feed.html", **context)


@app.route("/feed/<feed_id>/preview")
def preview_feed(feed_id):
    data = json.load(open(DATA_FILE))
    feed = list(filter(lambda feed: feed["id"] == feed_id, data["feeds"]))[0]

    data = feedparser.parse(feed["url"])
    if "bozo" in data:
        feed["exception"] = data["bozo_exception"]
    feed["entries"] = data["entries"]
    feed = Feed(feed)
    return render_template("preview_feed.html", feed=feed)
