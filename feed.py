# -*- coding: utf-8 -*-


import json


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
