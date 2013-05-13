from django.http import HttpResponse
import json

from entrouvert.wsgi import middleware

'''Version middleware to retrieves Entr'ouvert packages versions'''

class VersionMiddleware:
    def process_request(self, request):
        if request.method == 'GET' and request.path == '/__version__':
            packages_version = middleware.VersionMiddleware.get_packages_version()
            return HttpResponse(json.dumps(packages_version),
                    content_type='application/json')
        return None
