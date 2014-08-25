from django.core.management.base import BaseCommand
from entrouvert.djommon.multitenant.middleware import TenantMiddleware

class Command(BaseCommand):
    requires_model_validation = True
    can_import_settings = True
    option_list = BaseCommand.option_list

    def handle(self, **options):
        all_tenants = TenantMiddleware.get_tenants()

        for tenant in all_tenants:
            print("{0} {1}".format(tenant.schema_name, tenant.domain_url))

