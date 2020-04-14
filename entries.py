# -*- coding: utf-8 -*-


from urllib.parse import urlparse, urljoin

from bs4 import BeautifulSoup


class Property(object):
    def __init__(self, data):
        self.data = data

    def __getattr__(self, name):
        if name not in dir(self):
            if name not in self.data:
                raise AttributeError(
                    f"'{self.__class__.__name__}' object has no attribute '{name}'"
                )

            return self.data[name]


class Entry(Property):
    @property
    def summary(self):
        content = self.data["summary"]
        if content.startswith("<![CDATA["):
            content = content[9:-3]
        soup = BeautifulSoup(content, "html.parser")
        return soup.text

    @property
    def content(self):
        url = self.data["title_detail"]["base"]
        domain = "{url.scheme}://{url.netloc}".format(url=urlparse(url))

        contents = self.data.get("content", [{"value": ""}])
        for content in contents:
            soup = BeautifulSoup(content["value"], "html.parser")
            images = soup.find_all("img")
            for image in images:
                # ensure max width
                image["style"] = "max-width: 100%"
                # ensure full src path
                if image["src"].startswith("/"):
                    image["src"] = urljoin(domain, image["src"])
            content["value"] = soup.prettify()
        return contents

    @property
    def content_flat(self):
        return "".join([content["value"] for content in self.content])


class Feed(Property):
    @property
    def entries(self):
        entries = self.data["entries"]
        if self.data.get("filter"):
            entries = filter(lambda entry: self.data["filter"] in entry["title"], entries)
        return [Entry(entry) for entry in entries]
