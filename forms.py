# -*- coding: utf-8 -*-

from flask_wtf import FlaskForm
from wtforms import validators
from wtforms.fields import StringField
from wtforms.fields.html5 import URLField


class AddFeedForm(FlaskForm):
    url = URLField("URL", [validators.DataRequired(), validators.URL()])


class EditFeedForm(FlaskForm):
    url = URLField("URL", [validators.DataRequired(), validators.URL()])
    title = StringField("Title", [validators.DataRequired()])
    filter = StringField("Filter", [validators.Optional()])
