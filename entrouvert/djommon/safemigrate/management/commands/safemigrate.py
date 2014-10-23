from django.core.management.base import NoArgsCommand
from django.db import connection, models
from south.models import MigrationHistory

from django.core.management.commands.syncdb import Command as DjangoSyncdbCommand
from south.management.commands.syncdb import Command as SouthSyncdbCommand
from south.management.commands.migrate import Command as SouthMigrateCommand


class Command(NoArgsCommand):
    option_list = DjangoSyncdbCommand.option_list
    help = "syncdb and migrate the project, migrate '--fake app 0001' each app that has a new initial migration"

    def handle_noargs(self, *args, **options):
        verbosity = int(options['verbosity'])
        # step 1 : syncdb, create all apps without migrations
        SouthSyncdbCommand().execute(migrate_all=False, migrate=False, **options)
        # step 2 : detect and "fake 0001" all installed apps that had never
        # migrated (applications in database but not in south history)
        if verbosity > 0:
            print
        self.fake_if_needed(verbosity)
        # step 3 : migrate
        if verbosity > 0:
            print
        SouthMigrateCommand().execute(**options)

    def fake_if_needed(self, verbosity=1):
        # detect installed models
        # (code borrowed from django syncdb command)
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

        if verbosity > 0:
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

            if verbosity > 0:
                print ' - %s: %s' % (app.app_label(), status)
            if status == 'migration-is-new':
                if verbosity > 0:
                    print '   need fake migration to 0001_initial'
                # migrate --fake gdc 0001
                SouthMigrateCommand().execute(app=app.app_label(), target='0001', fake=True, verbosity=verbosity)
