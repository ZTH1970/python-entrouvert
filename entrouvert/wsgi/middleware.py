from urllib import quote
import json
import pkg_resources

class VersionMiddleware(object):
    ENTROUVERT_PACKAGES = [
            'wcs',
            'authentic2',
            'polynum',
            'appli_project',
            'passerelle',
            'docbow',
            'compte_agglo_montpellier',
            'nose',
    ]
    VERSION = 1

    def __init__(self, application):
        self.application = application

    def __call__(self, environ, start_response):
        path = ''
        path += quote(environ.get('SCRIPT_NAME', ''))
        path += quote(environ.get('PATH_INFO', ''))
        method = environ.get('REQUEST_METHOD', 'GET')
        if method == 'GET' and path == '/__version__':
            packages_version = {}
            for distribution in tuple(pkg_resources.WorkingSet()):
                project_name = distribution.project_name
                version = distribution.version
                if project_name in self.ENTROUVERT_PACKAGES:
                    packages_version[project_name] = version
            start_response('200 Ok', [('content-type', 'text/json')])
            return [json.dumps(packages_version)]
        return self.application(environ, start_response)
