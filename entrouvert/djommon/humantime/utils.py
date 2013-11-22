import datetime

from django.utils.translation import npgettext, pgettext

def datetime2human(dt, include_time=False, days_limit=7):
    '''Format a datetime object for human consumption'''
    if isinstance(dt, datetime.date):
        dt = datetime.datetime(year=dt.year, month=dt.month, day=dt.day)
        include_time = False
    else:
        time = dt.strftime('%H:%M')
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    date = dt.date()
    if date == today:
        if include_time:
            return pgettext('humantime', 'today at {0}').format(time)
        else:
            return pgettext('humantime', 'today')
    elif date == yesterday:
        if include_time:
            return pgettext('humantime', 'yesterday at {0}').format(time)
        else:
            return pgettext('humantime', 'yesterday')
    else:
        delta = (today - date).days
        if delta <= days_limit:
            return npgettext('humantime', '{0} day ago', '{0} days ago',
                    delta).format(delta)
        else:
            return npgettext('humantime', 'more than {0} day ago', 'more than {0} days ago',
                    days_limit).format(days_limit)
