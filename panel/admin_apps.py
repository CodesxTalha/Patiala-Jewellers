from django.contrib.admin.apps import AdminConfig


class PanelAdminConfig(AdminConfig):
    """Use the Patiala admin site (its own layout and dashboard) as the default admin."""
    default_site = "panel.site.PanelAdminSite"

    def ready(self):
        super().ready()                      # finds every app's admin.py, which registers Django's own Users and Groups ...
        from django.contrib import admin
        from django.contrib.auth import get_user_model
        from django.contrib.auth.models import Group
        for model in (get_user_model(), Group):          # ... and the panel's Users page replaces them
            if admin.site.is_registered(model):
                admin.site.unregister(model)
