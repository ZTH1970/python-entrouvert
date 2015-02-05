import os

from django.db import connection
from django.core.management.base import CommandError, BaseCommand

from entrouvert.djommon.multitenant.middleware import TenantMiddleware

class Command(BaseCommand):
    help = "Create tenant(s) by hostname(s)"

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))
        if not args:
            raise CommandError("you must give at least one tenant hostname")

        for hostname in args:
            try:
                tenant_base = TenantMiddleware.base()
            except AttributeError:
                raise CommandError("you must configure TENANT_BASE in your settings")
            if not tenant_base:
                raise CommandError("you must set a value to TENANT_BASE in your settings")
            tenant_dir = os.path.join(tenant_base, hostname)
            if not os.path.exists(tenant_dir):
                os.mkdir(tenant_dir, 0755)
            for folder in ('media', 'static', 'templates'):
                path = os.path.join(tenant_dir, folder)
                if not os.path.exists(path):
                    os.mkdir(path, 0755)
            connection.set_schema_to_public()
            tenant = TenantMiddleware.get_tenant_by_hostname(hostname)
            if verbosity >= 1:
                print
                print self.style.NOTICE("=== Creating schema ") \
                    + self.style.SQL_TABLE(tenant.schema_name)
            tenant.create_schema(check_if_exists=True)
