from tenant_schemas.models import TenantMixin

class Tenant(TenantMixin):
    # default true, schema will be automatically created and synced when it is saved
    auto_create_schema = False

    def save(self):
        pass

    def __unicode__(self):
        return u'%s' % self.schema_name
