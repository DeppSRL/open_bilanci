from django.core.cache import cache
from django.utils.translation import ugettext_lazy as _
from django.db import models
from tinymce.models import HTMLField

class Term(models.Model):
    """
    An idioticon is a glossary.

    It is used in popovers all over the website, and it may be used to build
    a proper glossary page.

    It is called idioticon, because it's a much more interesting name.
    """
    term = models.CharField(_("Term"), max_length=255,
                            help_text=_("The term"))
    slug = models.SlugField(max_length=255, unique=True, help_text=_("A single word or slug, to use as key in popovers' inclusion tags"))
    popover_title = models.CharField(_("Title"), max_length=255, blank=True, null=True,
                                     help_text=_("The title in the popover box"))
    definition = HTMLField(_("Definition"), help_text=_("The definition of the term"), blank=True)
    main_term = models.ForeignKey('self', null=True, blank=True, related_name='linked_terms', help_text=_("Main definition"))

    @property
    def is_main_term(self):
        return self.main_term is None

    def save(self, *args, **kwargs):
        if self.term == '':
            self.term = self.slug
        # expire cached value
        term_key = 'popover-%s' % self.slug
        if cache.get(term_key):
            cache.delete(term_key)
        return super(Term, self).save(*args, **kwargs)

    class Meta:
        verbose_name = _("Term")
        verbose_name_plural = _("Terms")

    def __unicode__(self):
        return self.term

