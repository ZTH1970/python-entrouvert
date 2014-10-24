# this file derive from django-tenant-schemas
#   Author: Bernardo Pires Carneiro
#   Email: carneiro.be@gmail.com
#   License: MIT license
#   Home-page: http://github.com/bcarneiro/django-tenant-schemas
from django.conf import settings
from django.db import connection
from south import migration
from south.migration.base import Migrations
from entrouvert.djommon.multitenant.middleware import TenantMiddleware
from entrouvert.djommon.multitenant.management.commands import SyncCommon
from entrouvert.djommon.management.commands.safemigrate import Command as SafeMigrateCommand
from entrouvert.djommon.multitenant.management.commands.sync_schemas import Command as MTSyncCommand
from entrouvert.djommon.multitenant.management.commands.migrate_schemas import Command as MTMigrateCommand


class Command(SyncCommon):
    help = "Safely migrate schemas with South"
    option_list = MTMigrateCommand.option_list

    def handle(self, *args, **options):
        super(Command, self).handle(*args, **options)

        MTSyncCommand().execute(*args, **options)
        connection.set_schema_to_public()
        if self.sync_public:
            self.fake_public_apps()
        if self.sync_tenant:
            self.fake_tenant_apps(self.domain)
        connection.set_schema_to_public()
        MTMigrateCommand().execute(*args, **options)

    def _set_managed_apps(self, included_apps, excluded_apps):
        """ while sync_schemas works by setting which apps are managed, on south we set which apps should be ignored """
        ignored_apps = []
        if excluded_apps:
            for item in excluded_apps:
                if item not in included_apps:
                    ignored_apps.append(item)

        for app in ignored_apps:
            app_label = app.split('.')[-1]
            settings.SOUTH_MIGRATION_MODULES[app_label] = 'ignore'

    def _save_south_settings(self):
        self._old_south_modules = None
        if hasattr(settings, "SOUTH_MIGRATION_MODULES") and settings.SOUTH_MIGRATION_MODULES is not None:
            self._old_south_modules = settings.SOUTH_MIGRATION_MODULES.copy()
        else:
            settings.SOUTH_MIGRATION_MODULES = dict()

    def _restore_south_settings(self):
        settings.SOUTH_MIGRATION_MODULES = self._old_south_modules

    def _clear_south_cache(self):
        for mig in list(migration.all_migrations()):
            delattr(mig._application, "migrations")
        Migrations._clear_cache()

    def _fake_schema(self, tenant):
        connection.set_tenant(tenant, include_public=False)
        SafeMigrateCommand().fake_if_needed()

    def fake_tenant_apps(self, schema_name=None):
        self._save_south_settings()

        apps = self.tenant_apps or self.installed_apps
        self._set_managed_apps(included_apps=apps, excluded_apps=self.shared_apps)

        if schema_name:
            self._notice("=== Running fake_if_needed for schema: %s" % schema_name)
            connection.set_schema_to_public()
            tenant = TenantMiddleware.get_tenant_by_hostname(schema_name)
            self._fake_schema(tenant)
        else:
            all_tenants = TenantMiddleware.get_tenants()
            if not all_tenants:
                self._notice("No tenants found")

            for tenant in all_tenants:
                Migrations._dependencies_done = False  # very important, the dependencies need to be purged from cache
                self._notice("=== Running fake_if_needed for schema %s" % tenant.schema_name)
                self._fake_schema(tenant)

        self._restore_south_settings()

    def fake_public_apps(self):
        self._save_south_settings()

        apps = self.shared_apps or self.installed_apps
        self._set_managed_apps(included_apps=apps, excluded_apps=self.tenant_apps)

        self._notice("=== Running fake_if_needed for schema public")
        SafeMigrateCommand().fake_if_needed()

        self._clear_south_cache()
        self._restore_south_settings()
