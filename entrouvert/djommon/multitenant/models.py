import re
import json

from django.utils.translation import ugettext as _
from django.db import models
from django.core.exceptions import ImproperlyConfigured, ValidationError

from tenant_schemas.models import TenantMixin

from . import app_settings

class Tenant(TenantMixin):
    name = models.CharField(max_length=100, verbose_name=_('name'))
    created_on = models.DateField(auto_now_add=True, verbose_name=_('created on'))
    is_active = models.BooleanField(default=True, blank=True, verbose_name=_('active'))

    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = False

    def __unicode__(self):
        return u'%s' % self.schema_name


class ClientSetting(models.Model):
    NAME_RE = re.compile(r'^[_A-Z][_A-Z0-9]*$')

    tenant = models.ForeignKey('Tenant', verbose_name=_('tenant'))
    name = models.CharField(max_length=100, verbose_name=_('name'))
    value = models.TextField(verbose_name=_('value'), help_text=_('JSON'))

    def get_json(self):
        return json.loads(self.value)

    def set_json(self, json):
        self.value = json.dumps(json)

    json = property(get_json, set_json)

    def clean(self):
        if not re.match(self.NAME_RE, self.name):
            raise ValidationError('name must be an uppercase variable '
                    'name')
        try:
            json.loads(self.value)
        except ValueError:
            raise ValidationError('invalid JSON document')
        if self.name in dir(app_settings):
            raise ImproperlyConfigured('The setting %r cannot be overridden by tenants' % self.name)

