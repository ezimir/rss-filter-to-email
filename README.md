# rss-filter-to-email

Reads entries from RSS feeds, filter them by title and sends them to selected email.

## Installation

Clone to `/path/to/rss-filter`, prepare virtual env, etc..

Install python packages with [pip-tools](https://pypi.org/project/pip-tools/):
```bash
$ pip-sync requirements.txt
```
or without:
```bash
$ pip install -r requirements.txt
```

Set environment variables:
```bash
export FLASK_ENV="production"
export FLASK_SECRET_KEY="some-random-string"

export MAIL_SERVER="localhost"
export MAIL_PORT=25
export MAIL_DOMAIN="outgoing_email.domain"
export MAIL_TO="target@email.com"
```

Run via flask:
```bash
$ flask run
```
or gunicorn:
```ini
[Unit]
Description=Gunicorn instance to serve RSS-filter
After=network.target

[Service]
User=www-data
Group=www-data
WorkingDirectory=/path/to/rss-filter
Environment="PATH=/path/to/rss-filter-virtualenv/bin"
EnvironmentFile=/path/to/rss-filter-virtualenv/envvars
ExecStart=/path/to/rss-filter-virtualenv/bin/gunicorn --bind unix:/tmp/rss-filter.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
```

Check every 15 minutes via cron:
```cron
export $(grep -v '^#' /path/to/rss-filter-virtualenv/envvars | grep -v '^$' | xargs) && cd /path/to/rss-filter/ && /path/to/rss-filter-virtualenv/bin/python process.py
```

Enjoy emails with new articles from selected RSS feeds.
