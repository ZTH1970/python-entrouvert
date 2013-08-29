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

# copied from http://stackoverflow.com/questions/9294043/include-django-logged-user-in-django-traceback-error

class UserInTracebackMiddleware(object):
    """
        Adds user details to request context during request processing, so that they
        show up in the error emails. Add to settings.MIDDLEWARE_CLASSES and keep it
        outermost(i.e. on top if possible). This allows it to catch exceptions in
        other middlewares as well.
    """

    def process_exception(self, request, exception):
        """
        Process the request to add some variables to it.
        """

        # Add other details about the user to the META CGI variables.
        try:
            if not request.user.is_authenticated():
                return
            if request.user.is_anonymous():
                request.META['AUTH_NAME'] = "Anonymous User"
                request.META['AUTH_USER'] = "Anonymous User"
                request.META['AUTH_USER_EMAIL'] = ""
                request.META['AUTH_USER_ID'] = 0
                request.META['AUTH_USER_IS_ACTIVE'] = False
                request.META['AUTH_USER_IS_SUPERUSER'] = False
                request.META['AUTH_USER_IS_STAFF'] = False
                request.META['AUTH_USER_LAST_LOGIN'] = ""
            else:
                request.META['AUTH_USER_ID'] = str(request.user.id)
                request.META['AUTH_NAME'] = str(request.user.first_name) + " " + str(request.user.last_name)
                request.META['AUTH_USER'] = str(request.user.username)
                request.META['AUTH_USER_EMAIL'] = str(request.user.email)
                request.META['AUTH_USER_IS_ACTIVE'] = str(request.user.is_active)
                request.META['AUTH_USER_IS_SUPERUSER'] = str(request.user.is_superuser)
                request.META['AUTH_USER_IS_STAFF'] = str(request.user.is_staff)
                request.META['AUTH_USER_LAST_LOGIN'] = str(request.user.last_login)
        except:
            pass
