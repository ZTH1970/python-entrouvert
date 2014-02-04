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
