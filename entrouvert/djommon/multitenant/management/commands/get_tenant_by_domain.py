from django.core.management.base import BaseCommand
from entrouvert.djommon.multitenant.middleware import TenantMiddleware

class Command(BaseCommand):
    help = "Create schemas"

    def handle(self, *args, **options):
        for arg in args:
            print TenantMiddleware.hostname2schema(arg)
