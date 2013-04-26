from entrouvert.wsgi.middleware import VersionMiddleware
from unittest import TestCase

class MiddlewareTestCase(TestCase):
    def setUp(self):
        VersionMiddleware.ENTROUVERT_PACKAGES.append('nose')

    def application(self, environ, start_response):
        start_response('coin', {'a':'b'})
        return ['xxx']

    def test_version_middleware(self):
        import json
        app = VersionMiddleware(self.application)
        class start_response_cls:
            status = None
            headers = None
            def __call__(self, status, headers):
                self.status = status
                self.headers = headers
        start_response = start_response_cls()
        result = app({ 'REQUEST_METHOD': 'GET', 'PATH_INFO': '/__version__'}, start_response)
        result = json.loads(''.join(result))
        self.assertTrue(type(result) is dict)
        self.assertTrue('nose' in result)
        result = app({ 'REQUEST_METHOD': 'GET', 'PATH_INFO': '/'}, start_response)
        self.assertEqual(result, ['xxx'])
        self.assertEqual(start_response.status, 'coin')
        self.assertEqual(start_response.headers, {'a': 'b'})

    def tearDown(self):
        VersionMiddleware.ENTROUVERT_PACKAGES.append('nose')
