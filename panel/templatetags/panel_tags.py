from django import template

from shop.templatetags.assets import versioned

register = template.Library()
register.simple_tag(versioned, name="asset")      # the same tag as the public site uses
