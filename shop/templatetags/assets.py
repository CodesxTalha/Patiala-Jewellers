import os

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static

register = template.Library()


def versioned(path):
    """A static file's URL with its modified time on the end, so browsers load the new file the moment it changes."""
    found = finders.find(path)
    version = int(os.path.getmtime(found)) if found else 0
    return f"{static(path)}?v={version}"


register.simple_tag(versioned, name="asset")
