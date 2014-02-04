import sys


class AppSettings:
    @property
    def settings(self):
        if not hasattr(self, '_settings'):
            from django.conf import settings
            self._settings = settings
        return self._settings

    @property
    def MULTITENANT_TEMPLATE_DIRS(self):
        return self.settings.MULTITENANT_TEMPLATE_DIRS


app_settings = AppSettings()
app_settings.__name__ = __name__
sys.modules[__name__] = app_settings
