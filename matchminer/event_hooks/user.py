import datetime
import logging

from matchminer import settings, database
from matchminer.templates.emails import emails


def email_user(items):

    # skip unless production.
    if settings.WELCOME_EMAIL != "YES":
        logging.debug("welcome email skipped")
        return

    # loop over each user.
    for user in items:

        # do not email users not approved by Susan
        if user['user_name'] == '':
            continue

        # generate email.
        recipient_email = user['email']

        # create the message.
        cur_date = datetime.date.today().strftime("%B %d, %Y")
        cur_stamp = datetime.datetime.now().strftime("%I:%M%p on %B %d, %Y")

        # generate text
        html = _user_email_text(user, cur_date, cur_stamp)

        db = database.get_db()
        email_item = {
            'email_from': settings.EMAIL_AUTHOR_PROTECTED,
            'email_to': recipient_email,
            'subject': 'Welcome to MatchMiner - %s' % cur_date,
            'body': html,
            'cc': [],
            'sent': False,
            'num_failures': 0,
            'errors': []
        }
        db['email'].insert(email_item)


def _user_email_text(user, cur_date, cur_stamp):
    html = '''<html><head></head><body>%s</body></html>''' % emails.ACCOUNT_APPROVAL_BODY.format(
        user['first_name'],
        user['last_name'],
        cur_stamp
    )
    return html
