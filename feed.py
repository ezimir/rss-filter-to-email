# -*- coding: utf-8 -*-


import json
import uuid
import feedparser

from bs4 import BeautifulSoup


class Feeds:
    def __init__(self, path):
        self.path = path
        self.read()

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

    def add(self, url):
        feed = feedparser.parse(url)
        title = feed.get("feed", {}).get("title", url)
        self.feeds.append(
            Feed({"id": str(uuid.uuid4()), "url": url, "title": title, "original": title})
        )
        self.save()

    def update(self, feed):
        for i, _ in enumerate(self.feeds):
            if feed.id == self.feeds[i].id:
                self.feeds[i] = feed
                break

        self.save()

    def delete(self, feed):
        ids = list([f.id for f in self.feeds])
        i = ids.index(feed.id)
        del self.feeds[i]
        self.save()

    def read(self):
        with open(self.path) as f:
            try:
                self.data = json.load(f)
            except json.decoder.JSONDecodeError:
                self.data = {"feeds": []}

            self.feeds = [Feed(f) for f in self.data["feeds"]]

    def save(self):
        with open(self.path, "w+") as f:
            f.truncate(0)
            self.data["feeds"] = [f.data for f in self.feeds]
            json.dump(self.data, f, indent=4)


class Feed:
    attrs = ["id", "url", "title", "filter", "original"]

    _feed = None
    _entries = None

    def __init__(self, data):
        self.data = data
        self.read()

    def read(self):
        for attr in self.attrs:
            setattr(self, attr, self.data.get(attr))

    def update(self, data):
        for attr in self.attrs:
            if attr in data:
                val = data.get(attr)
                self.data[attr] = val

        if "url" in data and data["url"] != self.url:
            self._feed = None
            self._entries = None

        self.read()

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
        "summary": "summary",
    }

    def __init__(self, data):
        self.data = data
        self.read()

    def read(self):
        for target, source in self.attrs.items():
            val = self.data.get(source)
            method_name = f"read_{target}"
            if hasattr(self, method_name):
                method = getattr(self, method_name)
                val = method(val)

            setattr(self, target, val)

    def read_summary(self, content):
        if content.startswith("<![CDATA["):
            content = content[9:-3]
        soup = BeautifulSoup(content, "html.parser")
        content = soup.text
        content = content.replace("Read full entry", "")
        return content

    def matches(self, text):
        return text in self.title
