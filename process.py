# -*- coding: utf-8 -*-



import feedparser
import json
import time

from datetime import datetime

from app import DATA_FILE



def get_dt(time_struct):
    return datetime.fromtimestamp(time.mktime(time_struct))


def run():
    data = json.load(open(DATA_FILE))

    now = datetime.now()
    print('Now: {}'.format(now))

    last_run = data.get('last_run')
    if last_run:
        last_run = get_dt(tuple(last_run))

    else:
        data['last_run'] = now.timetuple()
        with open(DATA_FILE, 'w+') as f:
            f.truncate(0)
            json.dump(data, f, indent = 4)

        return

    print('Last Run: {}'.format(now))
    print('Checking {} feeds...'.format(len(data['feeds'])))

    entries = []
    for feed in data['feeds']:
        response = feedparser.parse(feed['url'])
        new_entries = [entry for entry in response['entries'] if last_run < get_dt(entry['published_parsed'])]
        if len(new_entries):
            entries.extend((response['feed'], new_entries))

    print('New entries: {}.'.format(len(new_entries)))

if __name__ == '__main__':
    run()

