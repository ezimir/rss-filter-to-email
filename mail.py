# -*- coding: utf-8 -*-


import logging
import os
import smtplib

import email.message
import email.headerregistry


logging.basicConfig(format="%(asctime)s %(message)s", level=logging.INFO)


class Address(email.headerregistry.Address):
    def __init__(self, person):
        kwargs = {
            "addr_spec": person,
        }
        if isinstance(person, dict):
            kwargs.update({"display_name": person["name"], "addr_spec": person["address"]})

        super(Address, self).__init__(**kwargs)


def send_mail(author, recipient, subject, text, html):
    msg = email.message.EmailMessage()
    msg["From"] = Address(author)
    msg["To"] = [Address(recipient)]
    msg["Subject"] = subject

    msg.set_content(text)
    msg.add_alternative(html, subtype="html")

    try:
        server = smtplib.SMTP(os.environ.get("MAIL_SERVER"), os.environ.get("MAIL_PORT"))
        server.send_message(msg)

    except Exception as e:
        logging.error(f"Error when sending email:\n{e.__class__.__name__}: {e}")
