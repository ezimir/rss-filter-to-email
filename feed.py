# -*- coding: utf-8 -*-


import json


class Feeds:
    def __init__(self, path):
        with open(path) as f:
            self.data = json.load(f)
            self.feeds = [Feed(f) for f in self.data["feeds"]]

    def __iter__(self):
        self.i = 0
        return self

    def __next__(self):
        if self.i < len(self.feeds):
            feed = self.feeds[self.i]
            self.i += 1
            return feed

        raise StopIteration


class Feed:
    attrs = ["id", "url", "title", "filter"]

    def __init__(self, data):
        self.data = data
        for attr in self.attrs:
            setattr(self, attr, self.data.get(attr))
