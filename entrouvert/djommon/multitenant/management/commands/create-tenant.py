import re
import json
import sys

from optparse import make_option

from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify
from django.db import transaction


from ...models import ClientSetting


class Command(BaseCommand):
    requires_model_validation = True
    can_import_settings = True
    option_list = BaseCommand.option_list + (
            make_option('--list-settings',
                action='store_true',
                default=False,
                help='List settings'),
            make_option('--verbose',
                action='store_true',
                default=False,
                help='List settings'),
            make_option('--set-setting',
                action='append',
                default=[],
                help='Set setting, use key=value format'),
    )

    @transaction.commit_on_success
    def handle(self, domain_url, schema_name=None, **options):
        import tenant_schemas.utils

        tenant_model = tenant_schemas.utils.get_tenant_model()
        if schema_name is None:
            schema_name = slugify(domain_url)
        tenant, created = tenant_model.objects.get_or_create(domain_url=domain_url,
                defaults={'schema_name': schema_name})
        if created:
            print 'Created new tenant for', domain_url, 'and schema name', schema_name
        tenant.create_schema(True)
        if options['list_settings']:
            if tenant.clientsetting_set.exists():
                for client_setting in tenant.clientsetting_set.all():
                    print '{0.name}: {0.value}'.format(client_setting)
        for key_value in options['set_setting']:
            if '=' not in key_value:
                raise CommandError('invalid --set-settings %r', key_value)
            key, value = key_value.split('=', 1)
            if not re.match(ClientSetting.NAME_RE, key):
                raise CommandError('invalid --set-settings key %r', key)
            if value:
                try:
                    json.loads(value)
                except ValueError:
                    raise CommandError('invalid --set-settings value JSON %r', value)
                try:
                    client_setting = tenant.clientsetting_set.get(name=key)
                    client_setting.value = value
                    client_setting.save()
                    if options['verbose']:
                        print >>sys.stderr, 'Modified setting'
                except ClientSetting.DoesNotExist:
                    tenant.clientsetting_set.create(name=key, value=value)
                    if options['verbose']:
                        print >>sys.stderr, 'Created setting'
            else:
                qs = tenant.clientsetting_set.filter(name=key)
                count = qs.count()
                qs.delete()
                if options['verbose']:
                    if count:
                        print >>sys.stderr, 'Deleted settings'
                    else:
                        print >>sys.stderr, 'No setting found'
