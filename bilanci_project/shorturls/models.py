__author__ = 'stefano'
from django.db import models

class ShortUrl(models.Model):

    long_url = models.TextField(max_length=3000, null=False)
    short_url = models.TextField(max_length=1000, null=False)

