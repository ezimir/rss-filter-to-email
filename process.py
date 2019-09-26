# -*- coding: utf-8 -*-



import feedparser
import json
import os
import time

from datetime import datetime, timedelta
from email.utils import format_datetime
from urllib.parse import urlsplit

from app import DATA_FILE
from entries import Entry
from mail import send_mail



def get_dt(time_struct):
    try:
        return datetime.fromtimestamp(time.mktime(time_struct))
    except ValueError:
        return datetime.utcnow() - timedelta(days = 365)


def run():
    data = json.load(open(DATA_FILE))

    now = datetime.now()
    print('Now: {}'.format(now))

    last_run = data.get('last_run')

    data['last_run'] = now.timetuple()
    if last_run:
        last_run = get_dt(tuple(last_run))

    else:
        with open(DATA_FILE, 'w+') as f:
            f.truncate(0)
            json.dump(data, f, indent = 4)

        print('Saved last run date.')
        return

    print('Last Run: {}'.format(last_run))
    print('Checking {} feeds...'.format(len(data['feeds'])))

    entries = []
    for feed in data['feeds']:
        parse_args = {
            'modified': format_datetime(last_run),
        }
        if feed.get('etag'):
            parse_args['etag'] = feed['etag']

        response = feedparser.parse(feed['url'], **parse_args)
        print('\t{}: {}'.format(response.status, feed['url']))

        if hasattr(response, 'etag'):
            feed['etag'] = response.etag

        if response.status == 200:  # skip 304 for unmodified feeds
            new_entries = response['entries']
            # filter missing publish date
            new_entries = [entry for entry in new_entries if 'published_parsed' in entry]
            # filter malformed publish date
            new_entries = [entry for entry in new_entries if entry['published_parsed'].tm_year > 1]
            # filter entries from before last run
            new_entries = [entry for entry in new_entries if last_run < get_dt(entry['published_parsed'])]
            if len(new_entries):
                for new_entry in new_entries:
                    entries.append((feed, response['feed'], new_entry))

    MAIL_DOMAIN = os.environ.get('MAIL_DOMAIN')
    MAIL_TO = os.environ.get('MAIL_TO')

    if entries:
        print('New entries: {}.'.format(len(entries)))
        entries.sort(key = lambda entry: entry[2]['published_parsed'], reverse = True)
        for meta, feed, entry_data in entries:
            author = {
                'name': meta['title'],
                'address': '{}@{}'.format(
                    urlsplit(feed['link']).netloc,
                    MAIL_DOMAIN,
                ),
            }
            entry = Entry(entry_data)
            subject = entry.title
            text = entry.summary
            html = entry.content_flat

            print('Sending from {}...'.format(author['address']))
            send_mail(author, MAIL_TO, subject, text, html)

    else:
        print('No new entries.')

    with open(DATA_FILE, 'w+') as f:
        f.truncate(0)
        json.dump(data, f, indent = 4)


if __name__ == '__main__':
    run()

