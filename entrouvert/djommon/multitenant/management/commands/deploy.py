import urllib2
import json
import sys

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

from tenant_schemas.utils import tenant_context
from entrouvert.djommon.multitenant.middleware import TenantMiddleware

class Command(BaseCommand):
    help = 'Deploy a tenant from hobo'

    def handle(self, base_url, **options):
        environment = json.load(sys.stdin)
        for service in environment['services']:
            if service['base_url'] == base_url:
                break
        else:
            raise CommandError('Service %s not found' % base_url)
        hostname = urllib2.urlparse.urlsplit(base_url).netloc

        call_command('create_tenant', hostname)

        tenant_name = TenantMiddleware.hostname2schema(hostname)
        tenant = TenantMiddleware.get_tenant_by_hostname(tenant_name)
        with tenant_context(tenant):
            self.deploy_tenant(environment, service, options)

    def deploy_tenant(self, environment, service, options):
        pass
