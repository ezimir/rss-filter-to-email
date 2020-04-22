# -*- coding: utf-8 -*-


import jinja2
import logging
import requests
import time

from datetime import datetime, timedelta, timezone
from email.utils import format_datetime
from operator import attrgetter
from pathlib import Path
from urllib.parse import urlparse

from app import DATA_FILE, MAIL_DOMAIN, MAIL_TO
from feed import Feeds, Entry
from mail import send_mail


logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


def run():
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    logging.info(f"Now: {now}")

    feeds = Feeds(DATA_FILE)
    last_run = feeds.last_run

    if last_run is None:
        logging.warning("No last run, using 1 year ago...")
        last_run = now - timedelta(days=365)

    logging.info(f"Last run: {last_run}")
    logging.info(f"Checking {feeds.count()} feeds...")

    def is_recent(entry):
        for timestamp_key in Entry.timestamp_keys:
            if timestamp_key in entry:
                if entry[timestamp_key].tm_year < 1900:
                    # some feeds return unreasonably low year
                    return False

                entry_timestamp = datetime.fromtimestamp(
                    time.mktime(entry[timestamp_key]), timezone.utc
                )
                return entry_timestamp > last_run
        return False

    new_entries = []
    for feed in feeds:
        logging.info(f"\tChecking {feed.url} ...")
        parse_args = {"modified": format_datetime(last_run)}
        if feed.data.get("etag"):
            parse_args["etag"] = feed.data["etag"]
        response = feed.get_feed()  # **parse_args)
        if getattr(response, "status", None) == 304:
            logging.warning("\t\t304 not modified")
            continue

        entry_count = len(response["entries"])
        entries = [Entry(e, feed) for e in response["entries"] if is_recent(e)]
        if feed.filter:
            entries = [e for e in entries if e.matches(feed.filter)]
        logging.info(f"\t\tFound {len(entries)} recent entries out of {entry_count} total.")
        new_entries.extend(entries)

    if new_entries:
        recipient = MAIL_TO
        server_domain = MAIL_DOMAIN
        if not (recipient or server_domain):
            logging.error("Insufficient mail setup:")
            logging.error(f"\tto: {recipient}")
            logging.error(f"\tfrom: {server_domain}")
            return

        logging.info(f"Sending {len(new_entries)} messages.")
        new_entries.sort(key=attrgetter("timestamp"), reverse=True)

        base_dir = Path().resolve()
        template_dirs = [base_dir / loc for loc in ["templates", "static"]]
        env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_dirs))
        template = env.get_template("mail.html")
        for entry in new_entries:
            entry_domain = entry.domain
            if entry.domain != feed.domain:
                r = requests.get(entry.url)
                entry_domain = urlparse(r.url).netloc
            address = f"{entry_domain}@{server_domain}"
            author = {"name": entry.feed.title, "address": address}
            subject = entry.title

            text = f"Published: {entry.timestamp}\nURL: {entry.url}\n\n{entry.summary}"
            html = template.render({"entry": entry})

            logging.info(f"\t{address}: {subject}")
            send_mail(author, recipient, subject, text, html)

    else:
        logging.warning("No new entries found.")

    logging.info(f"Saving last run to: {now}")
    feeds.last_run = now
    feeds.save()
    return


if __name__ == "__main__":
    run()
