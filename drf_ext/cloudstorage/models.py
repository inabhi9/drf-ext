import os
from pathlib import Path

import django_boto.s3
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres import fields as pg_fields
from django.db import models, transaction
from django.utils.crypto import get_random_string
from django.utils.text import slugify

from drf_ext import utils
from drf_ext.cloudstorage.errors import UploadError
from drf_ext.db import Manager, Model


class StorageProviderMixin:
    @classmethod
    def upload(cls, f, directory, use_filename=True):
        raise NotImplementedError

    def create_and_upload(self, f, **kwargs):
        """
        :param filename f:
        :param kwargs:
            :bool use_filename:
            :content_type:
            :str content_field:
            :str target:
            :int object_id:
        :return:
        """
        content_type = kwargs.get('content_type') or None
        content_field = kwargs.get('content_field') or None
        target = kwargs.pop('target', None)
        link_content = kwargs.pop('link_content', False)
        use_filename = kwargs.pop('use_filename', False)

        assert target or (content_type and content_field)

        # resolve target
        if target:
            content_type, content_field = self._parse_target(target)
            kwargs.update({'content_type': content_type, 'content_field': content_field})

        upload_dir = self._contenttype_upload_dir(content_type, content_field)

        with transaction.atomic():
            kwargs.update({'url': '', 'upload_resp': None})
            cloudfile = self.create(**kwargs)

            url, resp = self.upload(f, upload_dir, use_filename=use_filename)
            cloudfile.url = url
            cloudfile.upload_resp = resp
            cloudfile.save()

            if link_content is True:
                cloudfile.link_to_content()

        return cloudfile

    @classmethod
    def _parse_target(cls, target):
        app_label, model, field = target.lower().split('.')

        content_type = ContentType.objects.get_by_natural_key(app_label, model)

        return content_type, field

    @classmethod
    def _contenttype_upload_dir(cls, contenttype, field=''):
        return '%s__%s__%s'.rstrip('_') % (contenttype.app_label, contenttype.model, field)

    @classmethod
    def _get_file_name(cls, f, use_filename):
        if isinstance(f, str):
            filename = utils.path_leaf(f)
        else:
            filename = f.name

        if use_filename is False:
            filename = '%s_%s' % (get_random_string(5), filename)

        # Slugify only file name without extension
        filename_, ext = os.path.splitext(filename)
        filename_ = slugify(filename_)
        ext = ''.join(Path(filename).suffixes)

        return '%s%s' % (filename_, ext)


class S3FileManager(Manager, StorageProviderMixin):
    @classmethod
    def upload(cls, f, directory, use_filename=False):
        filename = cls._get_file_name(f, use_filename)

        try:
            url = django_boto.s3.upload(f, name=filename, prefix=directory)
            resp = {'prefix': directory, 'name': filename, 'storage': 's3'}
            return url, resp
        except Exception as e:
            raise UploadError from e


class AbstractCloudFile(Model):
    """
    Class to store files metadata
    """
    name = models.CharField(max_length=50, default='', blank=True)
    #: Uploaded url
    url = models.URLField()
    #: response received from uploading service
    upload_resp = pg_fields.JSONField(blank=True, editable=False, null=True)
    #: Target model name
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE, blank=True)
    #: Represents the model field
    content_field = models.CharField(max_length=50, blank=True, null=True)
    #: Target object pk
    object_id = models.CharField(max_length=10, null=True)

    content_object = GenericForeignKey('content_type', 'object_id')

    #: User who uploads the file i.e. owner of the object
    owner = models.ForeignKey('user.User', default=None, blank=True, editable=False, null=True,
                              on_delete=models.SET_NULL)

    s3 = S3FileManager()

    class Meta(Model.Meta):
        db_table = 'cloudstorage_file'
        abstract = True

    @property
    def extra(self):
        return {}

    def link_to_content(self):
        """
        Sets foreign key or add to the object located by content_type, object_id and content_field

        :TODO: Validate field class having ForiegnKey/ManyToMany to this class.

        :return Model: Object that is linked
        """
        model_cls = self.content_type.model_class()
        field = model_cls._meta.get_field(self.content_field)
        has_many_files = isinstance(field, models.ManyToManyField)
        obj = model_cls.objects.get(pk=self.object_id)

        if has_many_files:
            getattr(obj, self.content_field).add(self)
        else:
            setattr(obj, self.content_field, self)
            obj.save(update_fields=[self.content_field])

        return obj

    def download(self):
        """

        :return TemporaryFile:
        """
        if self.upload_resp['storage'] == 's3':
            return django_boto.s3.download(self.upload_resp['name'], self.upload_resp['prefix'])

        raise NotImplementedError
