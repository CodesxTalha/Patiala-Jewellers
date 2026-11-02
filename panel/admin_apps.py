from django.contrib.admin.apps import AdminConfig


class PanelAdminConfig(AdminConfig):
    """Use the Patiala admin site (its own layout and dashboard) as the default admin."""
    default_site = "panel.site.PanelAdminSite"
