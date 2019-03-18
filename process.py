# -*- coding: utf-8 -*-



import feedparser
import json
import os
import time

from datetime import datetime
from email.utils import format_datetime
from urllib.parse import urlsplit

from app import DATA_FILE
from mail import send_mail



def get_dt(time_struct):
    return datetime.fromtimestamp(time.mktime(time_struct))


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

        return

    print('Last Run: {}'.format(now))
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
            new_entries = [entry for entry in response['entries'] if last_run < get_dt(entry['published_parsed'])]
            if len(new_entries):
                for new_entry in new_entries:
                    entries.append((response['feed'], new_entry))

    MAIL_DOMAIN = os.environ.get('MAIL_DOMAIN')
    MAIL_TO = os.environ.get('MAIL_TO')

    if entries:
        print('New entries: {}.'.format(len(entries)))
        entries.sort(key = lambda entry: entry[1]['published_parsed'], reverse = True)
        for feed, entry in entries:
            author = {
                'name': feed['title'],
                'address': '{}@{}'.format(
                    urlsplit(feed['link']).netloc,
                    MAIL_DOMAIN,
                ),
            }
            subject = entry['title']
            text = entry['summary']
            html = ''.join([content['value'] for content in entry['content']])

            print('Sending from {}...'.format(author['address']))
            send_mail(author, MAIL_TO, subject, text, html)

    else:
        print('No new entries.')

    with open(DATA_FILE, 'w+') as f:
        f.truncate(0)
        json.dump(data, f, indent = 4)

if __name__ == '__main__':
    run()
