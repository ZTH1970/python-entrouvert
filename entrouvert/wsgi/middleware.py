from urllib import quote
import json
import pkg_resources

class VersionMiddleware(object):
    ENTROUVERT_PACKAGES = [
            'wcs',
            'wcs-au-quotidien',
            'authentic2',
            'authentic2-idp-cas',
            'authentic2-idp-ltpa',
            'authentic2-idp-oauth2',
            'polynum',
            'appli_project',
            'passerelle',
            'docbow',
            'calebasse',
            'python-entrouvert',
            'nose',
            'portail-citoyen',
            'portail-citoyen2',
            'portail-citoyen-announces',
            'django-cms-ajax-text-plugin',
            'mandaye',
            'eopayment',
            'mandaye-cam',
            'mandaye-meyzieu',
            'mandaye-vincennes',
            'compte-meyzieu',
            'compte-agglo-montpellier',
            'compte-orleans',
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
            packages_version = self.get_packages_version()
            start_response('200 Ok', [('content-type', 'application/json')])
            return [json.dumps(packages_version)]
        return self.application(environ, start_response)

    @classmethod
    def get_packages_version(cls):
        packages_version = {}
        for distribution in tuple(pkg_resources.WorkingSet()):
            project_name = distribution.project_name
            version = distribution.version
            if project_name in cls.ENTROUVERT_PACKAGES:
                packages_version[project_name] = version
        return packages_version
