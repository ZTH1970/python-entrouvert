import datetime

from django.utils.translation import pgettext
from django.utils.timezone import localtime, get_default_timezone
from django.template.defaultfilters import date

def datetime2human(dt, include_time=False, days_limit=7):
    '''Format a datetime object for human consumption'''
    if isinstance(dt, datetime.datetime):
        dt = localtime(dt)
        time = dt.strftime('%H:%M')
    else:
        dt = datetime.datetime(year=dt.year, month=dt.month, day=dt.day,
                tzinfo=get_default_timezone())
        dt = localtime(dt)
        include_time = False
    today = datetime.date.today()
    yesterday = today - datetime.timedelta(days=1)
    subdate = dt.date()
    if subdate == today:
        if include_time:
            return pgettext('humantime', 'today at {0}').format(time)
        else:
            return pgettext('humantime', 'today')
    elif subdate == yesterday:
        if include_time:
            return pgettext('humantime', 'yesterday at {0}').format(time)
        else:
            return pgettext('humantime', 'yesterday')
    else:
        if include_time:
            return date(dt, 'SHORT_DATETIME_FORMAT')
        else:
            return date(dt, 'SHORT_DATE_FORMAT')
