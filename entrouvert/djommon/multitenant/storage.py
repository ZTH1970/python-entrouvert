import os

from django.conf import settings
from django.core.exceptions import SuspiciousOperation
from django.utils._os import safe_join

from django.db import connection

from django.core.files.storage import FileSystemStorage

__all__ = ('TenantFileSystemStorage', )

class TenantFileSystemStorage(FileSystemStorage):
    '''Lookup files first in $TENANT_BASE/<tenant.schema>/media/ then in default location'''
    def path(self, name):
        if connection.tenant:
            location = safe_join(settings.TENANT_BASE, connection.tenant.schema_name, 'media')
        else:
            location = self.location
        try:
            path = safe_join(location, name)
        except ValueError:
            raise SuspiciousOperation("Attempted access to '%s' denied." % name)
        return os.path.normpath(path)