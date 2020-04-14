# -*- coding: utf-8 -*-


import os

from pathlib import Path

from flask import Flask
from flask import request, flash, render_template, redirect, url_for
from flask_debugtoolbar import DebugToolbarExtension
from flask_wtf.csrf import CSRFProtect

import forms
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
    path = Path(DATA_FILE)
    if path.exists():
        context["feeds"] = Feeds(DATA_FILE)

    else:
        flash('Data file "{}" not found.'.format(DATA_FILE), "error")

    return render_template("home.html", **context)


@app.route("/add-feed", methods=["GET", "POST"])
def add():
    context = {}
    context["form"] = form = forms.AddFeedForm(request.form)
    if request.method == "POST" and form.validate():
        path = Path(DATA_FILE)
        if not path.exists():
            path.touch()
        feeds = Feeds(DATA_FILE)
        feeds.add(form.data["url"])
        flash("Feed saved!")
        return redirect(url_for("home"))
    return render_template("add.html", **context)


@app.route("/feed/<feed_id>", methods=["GET", "POST"])
def feed(feed_id):
    context = {}
    feeds = Feeds(DATA_FILE)
    context["feed"] = feed = feeds.get(feed_id)

    if feed is None:
        return redirect(url_for("home"))

    context["form"] = form = forms.EditFeedForm(request.form)
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
