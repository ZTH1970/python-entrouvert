"""
Test multitenant framework
"""

import tempfile
import shutil
import os
import json
import StringIO

from django.conf.urls import patterns
from django.test import TestCase, Client
from django.http import HttpResponse
from django.template.response import TemplateResponse

try:
    from django.test import override_settings
except ImportError: # django < 1.7
    from django.test.utils import override_settings


def json_key(request, *args, **kwargs):
    from django.conf import settings
    return HttpResponse(settings.JSON_KEY + ' json')

def python_key(request, *args, **kwargs):
    from django.conf import settings
    return HttpResponse(settings.PYTHON_KEY + ' python')

def template(request, *args, **kwargs):
    return TemplateResponse(request, 'tenant.html')

def upload(request):
    from django.core.files.storage import default_storage
    default_storage.save('upload', request.FILES['upload'])
    return HttpResponse('')

def download(request):
    from django.core.files.storage import default_storage
    return HttpResponse(default_storage.open('upload').read())

urlpatterns = patterns('',
        ('^json_key/$', json_key),
        ('^python_key/$', python_key),
        ('^template/$', template),
        ('^upload/$', upload),
        ('^download/$', download),
)

@override_settings(
        ROOT_URLCONF=__name__,
        MIDDLEWARE_CLASSES=(
            'entrouvert.djommon.multitenant.middleware.TenantMiddleware',
            'entrouvert.djommon.multitenant.middleware.JSONSettingsMiddleware',
            'entrouvert.djommon.multitenant.middleware.PythonSettingsMiddleware',
        ),
        TEMPLATE_LOADERS = (
           'entrouvert.djommon.multitenant.template_loader.FilesystemLoader',
        ),
        DEFAULT_FILE_STORAGE = 'entrouvert.djommon.multitenant.storage.TenantFileSystemStorage',
)
class SimpleTest(TestCase):
    TENANTS = ['tenant1', 'tenant2']

    def setUp(self):
        self.tenant_base = tempfile.mkdtemp()
        for tenant in self.TENANTS:
            tenant_dir = os.path.join(self.tenant_base, tenant)
            os.mkdir(tenant_dir)
            settings_py = os.path.join(tenant_dir, 'settings.json')
            with file(settings_py, 'w') as f:
                json.dump({'JSON_KEY': tenant}, f)
            settings_json = os.path.join(tenant_dir, 'settings.py')
            with file(settings_json, 'w') as f:
                print >>f, 'PYTHON_KEY = %r' % tenant
            templates_dir = os.path.join(tenant_dir, 'templates')
            os.mkdir(templates_dir)
            tenant_html = os.path.join(templates_dir, 'tenant.html')
            with file(tenant_html, 'w') as f:
                print >>f, tenant + ' template',
            media_dir = os.path.join(tenant_dir, 'media')
            os.mkdir(media_dir)

    def tearDown(self):
        shutil.rmtree(self.tenant_base, ignore_errors=True) 

    def tenant_settings(self):
        return self.settings(
                TENANT_BASE=self.tenant_base,
                TENANT_TEMPLATE_DIRS=(self.tenant_base,)
        )

    def test_tenants(self):
        with self.tenant_settings():
            for tenant in self.TENANTS:
                c = Client(HTTP_HOST=tenant)
                response = c.get('/json_key/')
                self.assertEqual(response.content, tenant + ' json')
                response = c.get('/python_key/')
                self.assertEqual(response.content, tenant + ' python')
                response = c.get('/template/')
                self.assertEqual(response.content, tenant + ' template')

    def test_list_tenants(self):
        from entrouvert.djommon.multitenant.middleware import TenantMiddleware
        from tenant_schemas.utils import get_tenant_model

        with self.tenant_settings():
            l1 = set(map(str, TenantMiddleware.get_tenants()))
            l2 = set(str(get_tenant_model()(schema_name=tenant,
                        domain_url=tenant)) for tenant in self.TENANTS)
            self.assertEquals(l1, l2)

    def test_storage(self):
        from django.core.files.base import ContentFile
        with self.tenant_settings():
            for tenant in self.TENANTS:
                c = Client(HTTP_HOST=tenant)
                uploaded_file_path = os.path.join(self.tenant_base, tenant, 'media', 'upload')
                self.assertFalse(os.path.exists(uploaded_file_path), uploaded_file_path)
                response = c.post('/upload/', {'upload': ContentFile(tenant + ' upload', name='upload.txt')})
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, '')
                self.assertTrue(os.path.exists(uploaded_file_path))
                self.assertEqual(file(uploaded_file_path).read(), tenant + ' upload')
                response = c.get('/download/')
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.content, tenant + ' upload')
