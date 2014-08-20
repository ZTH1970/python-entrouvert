from django.core.management.base import BaseCommand
from entrouvert.djommon.multitenant.middleware import TenantMiddleware
from django.db import connection

class Command(BaseCommand):
    help = "Create schemas"

    def handle(self, *args, **options):
        verbosity = int(options.get('verbosity'))

        connection.set_schema_to_public()
        all_tenants = TenantMiddleware.get_tenants()
        for tenant in all_tenants:
            if verbosity >= 1:
                print
                print self.style.NOTICE("=== Creating schema ") \
                    + self.style.SQL_TABLE(tenant.schema_name)

            if not tenant.create_schema(check_if_exists=True):
                print self.style.ERROR(' Nothing to do')
