"""
======
Models
======
Provides base models for other django.model subclass
"""

from django.db import models as df_models
from django.utils.translation import ugettext_lazy as _


class Manager(df_models.Manager):
    pass


class Model(df_models.Model):
    """
    Adds default permissions and some common methods
    .. note:: Always use this class instead of django.db.models.Model
    """
    created_at = df_models.DateTimeField(_('Created at'), auto_now_add=True)
    updated_at = df_models.DateTimeField(_('Updated at'), auto_now=True)

    objects = Manager()

    class Meta:
        default_permissions = ('add', 'change', 'delete', 'view')
        abstract = True
