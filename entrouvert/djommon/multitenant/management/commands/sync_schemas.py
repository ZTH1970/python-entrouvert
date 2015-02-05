# this file derive from django-tenant-schemas
#   Author: Bernardo Pires Carneiro
#   Email: carneiro.be@gmail.com
#   License: MIT license
#   Home-page: http://github.com/bcarneiro/django-tenant-schemas
import django
from django.core.management.base import CommandError

from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db.models import get_apps, get_models
if 'south' in settings.INSTALLED_APPS:
    from south.management.commands.syncdb import Command as SyncdbCommand
else:
    from django.core.management.commands.syncdb import Command as SyncdbCommand
from django.db import connection
from entrouvert.djommon.multitenant.middleware import TenantMiddleware
from entrouvert.djommon.multitenant.management.commands import SyncCommon


class Command(SyncCommon):
    help = "Sync schemas based on TENANT_APPS and SHARED_APPS settings"
    option_list = SyncdbCommand.option_list + SyncCommon.option_list

    def handle(self, *args, **options):
        if django.VERSION >= (1, 7, 0):
            raise CommandError('This command is only meant to be used for 1.6'
                               ' and older version of django. For 1.7, use'
                               ' `migrate_schemas` instead.')
        super(Command, self).handle(*args, **options)

        if "south" in settings.INSTALLED_APPS:
            self.options["migrate"] = False

        # save original settings
        for model in get_models(include_auto_created=True):
            setattr(model._meta, 'was_managed', model._meta.managed)

        ContentType.objects.clear_cache()

        if self.sync_public:
            self.sync_public_apps()
        if self.sync_tenant:
            self.sync_tenant_apps(self.domain)

        # restore settings
        for model in get_models(include_auto_created=True):
            model._meta.managed = model._meta.was_managed

    def _set_managed_apps(self, included_apps):
        """ sets which apps are managed by syncdb """
        for model in get_models(include_auto_created=True):
            model._meta.managed = False

        verbosity = int(self.options.get('verbosity'))
        for app_model in get_apps():
            app_name = app_model.__name__.replace('.models', '')
            if app_name in included_apps:
                for model in get_models(app_model, include_auto_created=True):
                    model._meta.managed = model._meta.was_managed
                    if model._meta.managed and verbosity >= 3:
                        self._notice("=== Include Model: %s: %s" % (app_name, model.__name__))

    def _sync_tenant(self, tenant):
        self._notice("=== Running syncdb for schema: %s" % tenant.schema_name)
        connection.set_tenant(tenant, include_public=False)
        SyncdbCommand().execute(**self.options)

    def sync_tenant_apps(self, schema_name=None):
        apps = self.tenant_apps or self.installed_apps
        self._set_managed_apps(apps)
        if schema_name:
            tenant = TenantMiddleware.get_tenant_by_hostname(schema_name)
            self._sync_tenant(tenant)
        else:
            all_tenants = TenantMiddleware.get_tenants()
            if not all_tenants:
                self._notice("No tenants found!")

            for tenant in all_tenants:
                self._sync_tenant(tenant)

    def sync_public_apps(self):
        self._notice("=== Running syncdb for schema public")
        apps = self.shared_apps or self.installed_apps
        self._set_managed_apps(apps)
        SyncdbCommand().execute(**self.options)
