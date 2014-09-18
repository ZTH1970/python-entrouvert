# this file derive from django-tenant-schemas
#   Author: Bernardo Pires Carneiro
#   Email: carneiro.be@gmail.com
#   License: MIT license
#   Home-page: http://github.com/bcarneiro/django-tenant-schemas
from optparse import make_option
from django.conf import settings
from django.core.management import call_command, get_commands, load_command_class
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
try:
    from django.utils.six.moves import input
except ImportError:
    input = raw_input
from tenant_schemas.utils import get_public_schema_name
from entrouvert.djommon.multitenant.middleware import TenantMiddleware


class BaseTenantCommand(BaseCommand):
    """
    Generic command class useful for iterating any existing command
    over all schemata. The actual command name is expected in the
    class variable COMMAND_NAME of the subclass.
    """
    def __new__(cls, *args, **kwargs):
        """
        Sets option_list and help dynamically.
        """
        obj = super(BaseTenantCommand, cls).__new__(cls, *args, **kwargs)

        app_name = get_commands()[obj.COMMAND_NAME]
        if isinstance(app_name, BaseCommand):
            # If the command is already loaded, use it directly.
            cmdclass = app_name
        else:
            cmdclass = load_command_class(app_name, obj.COMMAND_NAME)

        # inherit the options from the original command
        obj.option_list = cmdclass.option_list
        obj.option_list += (
            make_option("-d", "--domain", dest="domain"),
        )
        obj.option_list += (
            make_option("-p", "--skip-public", dest="skip_public", action="store_true", default=False),
        )

        # prepend the command's original help with the info about schemata iteration
        obj.help = "Calls %s for all registered schemata. You can use regular %s options. "\
                   "Original help for %s: %s" % (obj.COMMAND_NAME, obj.COMMAND_NAME, obj.COMMAND_NAME,
                                                 getattr(cmdclass, 'help', 'none'))
        return obj

    def execute_command(self, tenant, command_name, *args, **options):
        verbosity = int(options.get('verbosity'))

        if verbosity >= 1:
            print()
            print(self.style.NOTICE("=== Switching to schema '") \
                + self.style.SQL_TABLE(tenant.schema_name)\
                + self.style.NOTICE("' then calling %s:" % command_name))

        connection.set_tenant(tenant)

        # call the original command with the args it knows
        call_command(command_name, *args, **options)

    def handle(self, *args, **options):
        """
        Iterates a command over all registered schemata.
        """
        if options['domain']:
            # only run on a particular schema
            connection.set_schema_to_public()
            self.execute_command(TenantMiddleware.get_tenant_by_hostname(options['domain']), self.COMMAND_NAME, *args, **options)
        else:
            for tenant in TenantMiddleware.get_tenants():
                if not(options['skip_public'] and tenant.schema_name == get_public_schema_name()):
                    self.execute_command(tenant, self.COMMAND_NAME, *args, **options)


class InteractiveTenantOption(object):
    def __init__(self, *args, **kwargs):
        super(InteractiveTenantOption, self).__init__(*args, **kwargs)
        self.option_list += (
            make_option("-d", "--domain", dest="domain", help="specify tenant domain"),
        )

    def get_tenant_from_options_or_interactive(self, **options):
        all_tenants = list(TenantMiddleware.get_tenants())

        if not all_tenants:
            raise CommandError("""There are no tenants in the system.
To learn how create a tenant, see:
https://django-tenant-schemas.readthedocs.org/en/latest/use.html#creating-a-tenant""")

        if options.get('domain'):
            tenant_schema = options['domain']
        else:
            while True:
                tenant_schema = input("Enter Tenant Domain ('?' to list schemas): ")
                if tenant_schema == '?':
                    print('\n'.join(["%s - %s" % (t.schema_name, t.domain_url,) for t in all_tenants]))
                else:
                    break

        if tenant_schema not in [t.schema_name for t in all_tenants]:
            raise CommandError("Invalid tenant schema, '%s'" % (tenant_schema,))

        return TenantMiddleware.get_tenant_by_hostname(tenant_schema)


class TenantWrappedCommand(InteractiveTenantOption, BaseCommand):
    """
    Generic command class useful for running any existing command
    on a particular tenant. The actual command name is expected in the
    class variable COMMAND_NAME of the subclass.
    """
    def __new__(cls, *args, **kwargs):
        obj = super(TenantWrappedCommand, cls).__new__(cls, *args, **kwargs)
        obj.command_instance = obj.COMMAND()
        obj.option_list = obj.command_instance.option_list
        return obj

    def handle(self, *args, **options):
        tenant = self.get_tenant_from_options_or_interactive(**options)
        connection.set_tenant(tenant)

        self.command_instance.execute(*args, **options)


class SyncCommon(BaseCommand):
    option_list = (
        make_option('--tenant', action='store_true', dest='tenant', default=False,
                    help='Tells Django to populate only tenant applications.'),
        make_option('--shared', action='store_true', dest='shared', default=False,
                    help='Tells Django to populate only shared applications.'),
        make_option("-d", "--domain", dest="domain"),
    )

    def handle(self, *args, **options):
        self.sync_tenant = options.get('tenant')
        self.sync_public = options.get('shared')
        self.domain = options.get('domain')
        self.installed_apps = settings.INSTALLED_APPS
        self.args = args
        self.options = options

        if self.domain:
            if self.sync_public:
                raise CommandError("schema should only be used with the --tenant switch.")
            elif self.domain == get_public_schema_name():
                self.sync_public = True
            else:
                self.sync_tenant = True
        elif not self.sync_public and not self.sync_tenant:
            # no options set, sync both
            self.sync_tenant = True
            self.sync_public = True

        if hasattr(settings, 'TENANT_APPS'):
            self.tenant_apps = settings.TENANT_APPS
        if hasattr(settings, 'SHARED_APPS'):
            self.shared_apps = settings.SHARED_APPS

    def _notice(self, output):
        self.stdout.write(self.style.NOTICE(output))
