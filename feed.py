# -*- coding: utf-8 -*-


import json
import feedparser
import html
import re
import requests
import tempfile
import uuid
import time

from datetime import datetime, timezone
from urllib.parse import urlparse, urljoin


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

    @property
    def last_run(self):
        if "last_run" not in self.data:
            return None

        val = tuple(self.data["last_run"])
        return datetime.fromtimestamp(time.mktime(val), timezone.utc)

    @last_run.setter
    def last_run(self, timestamp):
        self.data["last_run"] = timestamp.timetuple()

    def count(self):
        return len(self.feeds)

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

    def get_fixed_xml(self):
        r = requests.get(self.url)
        try:
            r.encoding = r.apparent_encoding
            xml = r.text.encode(r.encoding, "backslashreplace").decode("utf8", "replace")
        except (UnicodeDecodeError, UnicodeEncodeError):
            return ""

        xml = xml.replace("\n", "")

        def escape(match):
            return (
                "<description>&lt;![CDATA[" + html.escape(match.group(1)) + "]]&gt;</description>"
            )

        offset = 0
        for match in re.finditer(r"<item>.*?<description>(.*?)</description>.*?</item>", xml):
            match_xml = match.group()
            original = len(match_xml)
            match_xml = re.sub("<description>(.*?)</description>", escape, match_xml)
            start = match.start() + offset
            end = match.end() + offset
            xml = xml[:start] + match_xml + xml[end:]
            offset += len(match_xml) - original

        return xml.encode("utf8")

    def get_feed(self, **parse_args):
        feed = feedparser.parse(self.url, **parse_args)

        if hasattr(feed, "etag"):
            self.data["etag"] = feed.etag

        exc = feed.get("bozo_exception")
        if exc and "undefined entity" in exc.getMessage():
            with tempfile.NamedTemporaryFile(delete=False) as f:
                f.write(self.get_fixed_xml())
                feed = feedparser.parse(f.name)

        return feed

    @property
    def domain(self):
        return urlparse(self.url).netloc

    @property
    def entries(self):
        if self._feed is None:
            self._feed = self.get_feed()

        if self._entries is None:
            self._entries = [Entry(e, self) for e in self._feed["entries"]]

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
        "published": "published",
        "updated": "updated",
        "summary": "summary",
        "_content": "content",
    }

    timestamp_keys = ["published_parsed", "updated_parsed"]

    summary_treshold = 1000

    def __init__(self, data, feed):
        self.data = data
        self.feed = feed
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
        if len(content) > self.summary_treshold:
            first_paragraph = soup.find("p")
            if first_paragraph:
                content = first_paragraph.text
            elif "." in content:
                content = content.split(".")[0]
            else:
                content = content[: self.summary_treshold]
        content = content.replace("Read full entry", "")
        return content

    def read__content(self, content):
        if content is None:
            summary = self.data["summary"]
            if summary.startswith("<![CDATA["):
                summary = summary[9:-3]
            return [{"value": summary}]
        return content

    def matches(self, text):
        return text.lower() in self.title.lower()

    @property
    def timestamp(self):
        val = None
        for key in self.timestamp_keys:
            if key in self.data:
                val = self.data[key]

        if val is None:
            val = datetime.utcnow().replace(tzinfo=timezone.utc).timetuple()

        try:
            return datetime.fromtimestamp(time.mktime(val), timezone.utc)

        except ValueError:
            pass

    @property
    def domain(self):
        return urlparse(self.url).netloc

    @property
    def content(self):
        url = urlparse(self.url)
        prefix_base = f"{url.scheme}://{url.netloc}"
        prefix_entry = f"{url.scheme}://{url.netloc}{url.path}"

        content = self._content
        for item in content:
            soup = BeautifulSoup(item["value"], "html.parser")
            images = soup.find_all("img")
            for image in images:
                # ensure max width
                image["style"] = "max-width: 100%"
                # ensure full src path
                if not image["src"].startswith("http"):
                    prefix = prefix_base if image["src"].startswith("/") else prefix_entry
                    image["src"] = urljoin(prefix, image["src"])
            item["value"] = soup.prettify()
        return content
