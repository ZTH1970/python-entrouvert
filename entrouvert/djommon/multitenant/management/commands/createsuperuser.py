# this file derive from django-tenant-schemas
#   Author: Bernardo Pires Carneiro
#   Email: carneiro.be@gmail.com
#   License: MIT license
#   Home-page: http://github.com/bcarneiro/django-tenant-schemas
from entrouvert.djommon.multitenant.management.commands import TenantWrappedCommand
from django.contrib.auth.management.commands import createsuperuser


class Command(TenantWrappedCommand):
    COMMAND = createsuperuser.Command
