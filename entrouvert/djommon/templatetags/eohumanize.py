from django import template
from django.utils.safestring import mark_safe
from django.utils.html import escape
from django.utils.translation import pgettext


register = template.Library()


def widowless(value):
    '''Replace normal spaces by non-breakable spaces'''
    bits = escape(value).rsplit(' ', 1)
    try:
        return mark_safe(u'&nbsp;'.join(bits))
    except:
        return value
register.filter(widowless)


def nonbreakinghyphen(value):
    '''Replace normal hyphen by non-breaking version'''
    return value.replace('-', '&#8209;')
register.filter(nonbreakinghyphen)


def humanlist(value):
    '''Format a list of string-like objects for human reading'''
    if len(value) == 1:
        return unicode(value[0])
    elif len(value) > 1:
        first_part = pgettext('list formation', ', ').join(map(unicode, value[:-1]))
        last_part = unicode(value[-1])
        return pgettext('list formation', u'{first_part} and {last_part}').format(first_part=first_part,
                last_part=last_part)
register.filter(humanlist)


def ellipsize(value, length=25):
    '''Truncate string and add an ellipsis to its end if it is longer than
       length.

       Default length is 25 characters.'''
    if len(value) > length:
        value = value[:length] + '&#8230;'
    return value
register.filter(ellipsize)
