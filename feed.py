# -*- coding: utf-8 -*-


import json
import feedparser


class Feeds:
    def __init__(self, path):
        self.path = path
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

    def get(self, feed_id):
        for feed in self.feeds:
            if feed.id == feed_id:
                return feed

    def update(self, feed):
        for i, _ in enumerate(self.data["feeds"]):
            if feed.id == self.data["feeds"][i]["id"]:
                self.data["feeds"][i] = feed.data
                break

        self.save()

    def save(self):
        with open(self.path, "w+") as f:
            f.truncate(0)
            json.dump(self.data, f, indent=4)


class Feed:
    attrs = ["id", "url", "title", "filter", "original"]

    _feed = None
    _entries = None

    def __init__(self, data):
        self.data = data
        for attr in self.attrs:
            setattr(self, attr, self.data.get(attr))

    def update(self, data):
        for attr in self.attrs:
            if attr in data:
                val = data.get(attr)
                self.data[attr] = val
                setattr(self, attr, val)

    @property
    def entries(self):
        if self._feed is None:
            self._feed = feedparser.parse(self.url)

        if self._entries is None:
            self._entries = [Entry(e) for e in self._feed["entries"]]

        return self._entries

    @property
    def filtered(self):
        entries = self.entries
        if self.filter:
            entries = [e for e in entries if e.matches(self.filter)]
        return entries


class Entry:
    attrs = {
        "id": "id",
        "title": "title",
        "url": "link",
        "updated": "published",
    }

    def __init__(self, data):
        self.data = data
        for target, source in self.attrs.items():
            setattr(self, target, self.data.get(source))

    def matches(self, text):
        return text in self.title
