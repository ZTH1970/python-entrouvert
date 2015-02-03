import os
import json
import glob

from django.conf import settings, UserSettingsHolder
from django.db import connection
from django.http import Http404
from django.contrib.contenttypes.models import ContentType
from tenant_schemas.utils import get_tenant_model, remove_www_and_dev, get_public_schema_name

SENTINEL = object()

class TenantNotFound(RuntimeError):
    pass

class TenantMiddleware(object):
    """
    This middleware should be placed at the very top of the middleware stack.
    Selects the proper database schema using the request host. Can fail in
    various ways which is better than corrupting or revealing data...
    """
    @classmethod
    def base(cls):
        return settings.TENANT_BASE

    @classmethod
    def hostname2schema(cls, hostname):
        '''Convert hostname to PostgreSQL schema name'''
        if hostname in getattr(settings, 'TENANT_MAPPING', {}):
            return settings.TENANT_MAPPING[hostname]
        return hostname.replace('.', '_').replace('-', '_')

    @classmethod
    def get_tenant_by_hostname(cls, hostname):
        '''Retrieve a tenant object for this hostname'''
        if not os.path.exists(os.path.join(cls.base(), hostname)):
            raise TenantNotFound
        schema = cls.hostname2schema(hostname)
        return get_tenant_model()(schema_name=schema, domain_url=hostname)

    @classmethod
    def get_tenants(cls):
        self = cls()
        for path in glob.glob(os.path.join(cls.base(), '*')):
            hostname = os.path.basename(path)
            yield get_tenant_model()(
                    schema_name=self.hostname2schema(hostname),
                    domain_url=hostname)

    def process_request(self, request):
        # connection needs first to be at the public schema, as this is where the
        # tenant informations are saved
        connection.set_schema_to_public()
        hostname_without_port = remove_www_and_dev(request.get_host().split(':')[0])

        try:
            request.tenant = self.get_tenant_by_hostname(hostname_without_port)
        except TenantNotFound:
            raise Http404
        connection.set_tenant(request.tenant)

        # content type can no longer be cached as public and tenant schemas have different
        # models. if someone wants to change this, the cache needs to be separated between
        # public and shared schemas. if this cache isn't cleared, this can cause permission
        # problems. for example, on public, a particular model has id 14, but on the tenants
        # it has the id 15. if 14 is cached instead of 15, the permissions for the wrong
        # model will be fetched.
        ContentType.objects.clear_cache()

        # do we have a public-specific token?
        if hasattr(settings, 'PUBLIC_SCHEMA_URLCONF') and request.tenant.schema_name == get_public_schema_name():
            request.urlconf = settings.PUBLIC_SCHEMA_URLCONF




class TenantSettingBaseMiddleware(object):
    '''Base middleware classe for loading settings based on tenants

       Child classes MUST override the load_tenant_settings() method.
    '''
    def __init__(self, *args, **kwargs):
        self.tenants_settings = {}

    def get_tenant_settings(self, wrapped, tenant):
        '''Get last loaded settings for tenant, try to update it by loading
           settings again is last loading time is less recent thant settings data
           store. Compare with last modification time is done in the
           load_tenant_settings() method.
        '''
        tenant_settings, last_time = self.tenants_settings.get(tenant.schema_name, (None,None))
        if tenant_settings is None:
            tenant_settings = UserSettingsHolder(wrapped)
        tenant_settings, last_time = self.load_tenant_settings(wrapped, tenant, tenant_settings, last_time)
        self.tenants_settings[tenant.schema_name] = tenant_settings, last_time
        return tenant_settings

    def load_tenant_settings(self, wrapped, tenant, tenant_settings, last_time):
        '''Load tenant settings into tenant_settings object, eventually skip if
           last_time is more recent than last update time for settings and return
           the new value for tenant_settings and last_time'''
        raise NotImplemented

    def process_request(self, request):
        if not hasattr(request, '_old_settings_wrapped'):
            request._old_settings_wrapped = []
        request._old_settings_wrapped.append(settings._wrapped)
        settings._wrapped = self.get_tenant_settings(settings._wrapped, request.tenant)

    def process_response(self, request, response):
        if hasattr(request, '_old_settings_wrapped') and request._old_settings_wrapped:
            settings._wrapped = request._old_settings_wrapped.pop()
        return response


class FileBasedTenantSettingBaseMiddleware(TenantSettingBaseMiddleware):
    FILENAME = None

    def load_tenant_settings(self, wrapped, tenant, tenant_settings, last_time):
        path = os.path.join(settings.TENANT_BASE, tenant.domain_url, self.FILENAME)
        try:
            new_time = os.stat(path).st_mtime
        except OSError:
            # file was removed
            if not last_time is None:
                return UserSettingsHolder(wrapped), None
        else:
            if last_time is None or new_time >= last_time:
                # file is new
                tenant_settings = UserSettingsHolder(wrapped)
                self.load_file(tenant_settings, path)
                return tenant_settings, new_time
        # nothing has changed
        return tenant_settings, last_time


class JSONSettingsMiddleware(FileBasedTenantSettingBaseMiddleware):
    '''Load settings from a JSON file whose path is given by:

            os.path.join(settings.TENANT_BASE % schema_name, 'settings.json')

       The JSON file must be a dictionnary whose key/value will override
       current settings.
    '''
    FILENAME = 'settings.json'

    def load_file(sef, tenant_settings, path):
        with file(path) as f:
            json_settings = json.load(f)
            for key in json_settings:
                setattr(tenant_settings, key, json_settings[key])


class DictAdapter(dict):
    '''Give dict interface to plain objects'''
    def __init__(self, wrapped):
        self.wrapped = wrapped

    def __setitem__(self, key, value):
        setattr(self.wrapped, key, value)

    def __getitem__(self, key):
        try:
            return getattr(self.wrapped, key)
        except AttributeError:
            raise KeyError


class PythonSettingsMiddleware(FileBasedTenantSettingBaseMiddleware):
    '''Load settings from a file whose path is given by:

            os.path.join(settings.TENANT_BASE % schema_name, 'settings.py')

       The file is executed in the same context as the classic settings file
       using execfile.
    '''
    FILENAME = 'settings.py'

    def load_file(self, tenant_settings, path):
        execfile(path, DictAdapter(tenant_settings))
