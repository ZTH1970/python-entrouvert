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
        with tenant_context(tenant_name):
            self.deploy_tenant(environment, service)

    def deploy_tenant(self, options, environment, service):
        pass
