from django import template
from django.utils.timezone import localtime, get_default_timezone
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.template.defaultfilters import date

from .. import utils

register = template.Library()

@register.filter
def humandate(dt):
    full_dt = date(dt, 'SHORT_DATE_FORMAT')
    s = u'<span title="{0}">{1}</span>'.format(
            escape(full_dt), escape(utils.datetime2human(dt)))
    return mark_safe(s)

@register.filter
def humantime(dt):
    dt = localtime(dt)
    full_dt = date(dt, 'SHORT_DATETIME_FORMAT')
    s = u'<span title="{0}">{1}</span>'.format(
            escape(full_dt), escape(utils.datetime2human(dt, include_time=True)))
    return mark_safe(s)

