import os
import json

from django.conf import settings, UserSettingsHolder

from tenant_schemas.middleware import TenantMiddleware

SENTINEL = object()

class EOTenantMiddleware(TenantMiddleware):
    def __init__(self, *args, **kwargs):
        self.wrapped = settings._wrapped

    def process_request(self, request):
        super(EOTenantMiddleware, self).process_request(request)
        override = UserSettingsHolder(self.wrapped)
        for client_settings in request.tenant.clientsetting_set.all():
            setattr(override, client_settings.name, client_settings.json)
        settings._wrapped = override

    def process_response(self, request, response):
        settings._wrapped = self.wrapped
        return response

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
        path = os.path.join(settings.TENANT_BASE, tenant.schema_name, self.FILENAME)
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


class PythonSettingsMiddleware(JSONSettingsMiddleware):
    '''Load settings from a file whose path is given by:

            os.path.join(settings.TENANT_BASE % schema_name, 'settings.py')

       The file is executed in the same context as the classic settings file
       using execfile.
    '''
    FILENAME = 'settings.py'

    def load_file(self, tenant_settings, path):
        execfile(path, DictAdapter(tenant_settings))
