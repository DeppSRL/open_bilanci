from django import template
from django.utils.translation import ugettext_lazy as _
from django.core.exceptions import ObjectDoesNotExist
from idioticon.models import Term

register = template.Library()

@register.inclusion_tag('popover_enabled_icon.html')
def popover_info(term_slug, popover_placement='right', width='300px'):
    try:
        term = Term.objects.select_related('main_term').get(slug=term_slug)
        if term.main_term:
            term = term.main_term
    except ObjectDoesNotExist:
        return {
            'title': term_slug,
            'content': _("<em>Term not yet defined.</em>"),
            'placement': popover_placement,
            'width': width
        }


    return {
        'title': term.popover_title if term.popover_title is not None else term.term,
        'content': term.definition,
        'placement': popover_placement,
        'width': width
    }
