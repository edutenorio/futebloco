# Source:
# https://gist.github.com/Pacek/2327524

from django import template
from django.template.defaultfilters import urlencode, force_escape
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter()
def gmaplink(query):
    """
    Simple Django template filter that converts string (address, ...) to Google maps link

    Sample usage:
    "object.address" could be "Baker Street 32, London, United Kingdom"
    <a href="{{ object.address|gmaplink }}">View on Google Maps</a>
    Will result in:
    <a href="http://maps.google.com/maps?t=m&amp;q=Baker%20Street%2032%2C%20London%2C%0D%0AUnited%20Kingdom">
        View on Google Maps
    </a>
    """
    return mark_safe(
        'http://maps.google.com/maps?t=m&amp;q=%s' % urlencode(
            force_escape(query)
        )
    )
