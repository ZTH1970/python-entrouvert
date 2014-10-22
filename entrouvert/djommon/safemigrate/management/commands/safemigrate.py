from django.core.management.base import NoArgsCommand
from django.db import connections, router, models

from south.models import MigrationHistory
from south.management.commands import syncdb, migrate
from django.core.management.commands import syncdb as django_syncdb


class Command(NoArgsCommand):
    option_list = django_syncdb.Command.option_list
    help = '''syncdb + migrate, with "migrate --fake app 0001" for apps with new initial migrations'''

    def handle_noargs(self, *args, **options):

        # step 1 : syncdb, create all apps without migrations
        syncdb.Command().execute(migrate_all=False, migrate=False, **options)

        # step 2 : detect and "fake 0001" all installed apps that had never
        # migrated (applications in database but not in south history)

        # detect installed models
        # (code borrowed from django syncdb command)
        db = options.get('database')
        connection = connections[db]
        cursor = connection.cursor()
        tables = connection.introspection.table_names()
        def model_in_database(model):
            opts = model._meta
            converter = connection.introspection.table_name_converter
            return (converter(opts.db_table) in tables) or \
                (opts.auto_created and converter(opts.auto_created._meta.db_table) in tables)

        # list all applications with south migration
        # (code borrowed from south migrate command)
        from south import migration
        apps = list(migration.all_migrations())
        applied_migrations = MigrationHistory.objects.filter(app_name__in=[app.app_label() for app in apps])
        applied_migrations_lookup = dict(('%s.%s' % (mi.app_name, mi.migration), mi) for mi in applied_migrations)

        print
        print 'Status after syncdb:'

        for app in apps:
            # for each app with migrations, list already applied migrations
            applied_migrations = []
            for migration in app:
                full_name = migration.app_label() + "." + migration.name()
                if full_name in applied_migrations_lookup:
                    applied_migration = applied_migrations_lookup[full_name]
                    if applied_migration.applied:
                        applied_migrations.append(migration.name())

            # try all models in database, if there none, the application is new
            # (because south syncdb does not create any tables)
            new = True
            for m in models.get_models(app.get_application().models):
                if model_in_database(m):
                    new = False
                    break

            if new:
                status = 'application-is-new'
            elif not applied_migrations:
                status = 'migration-is-new'
            else:
                status = 'normal'

            print ' - %s: %s' % (app.app_label(), status)

            if status == 'migration-is-new':
                print '   need fake migration to 0001_initial'
                # migrate --fake gdc 0001
                migrate.Command().execute(app=app.app_label(), target='0001', fake=True)

        print
        migrate.Command().execute(**options)
