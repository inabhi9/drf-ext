"""
=======
ViewSet
=======
"""
import mimetypes
import os

from django.http import QueryDict, HttpResponse
from rest_framework import generics as rf_generics, viewsets as rf_viewsets
from rest_framework_extensions.mixins import NestedViewSetMixin as _NestedViewSetMixin


class GenericAPIView(rf_generics.GenericAPIView):
    @classmethod
    def attachment_response(cls, file, request, remove_file=True):
        filename = os.path.basename(file)
        with open(file, 'rb') as fp:
            response = HttpResponse(fp.read())

        type_, encoding = mimetypes.guess_type(file)
        if type_ is None:
            type_ = 'application/octet-stream'

        response['Content-Type'] = type_
        response['Content-Length'] = str(os.stat(file).st_size)
        if encoding is not None:
            response['Content-Encoding'] = encoding

        # To inspect details for the below code, see http://greenbytes.de/tech/tc2231/
        if u'WebKit' in request.META['HTTP_USER_AGENT']:
            # Safari 3.0 and Chrome 2.0 accepts UTF-8 encoded string directly.
            filename_header = 'filename=%s' % filename
        elif u'MSIE' in request.META['HTTP_USER_AGENT']:
            # IE does not support internationalized filename at all.
            # It can only recognize internationalized URL, so we do the trick via routing rules.
            filename_header = ''
        else:
            # For others like Firefox, we follow RFC2231 (encoding extension in HTTP headers).
            filename_header = 'filename*=UTF-8\'\'%s' % filename

        response['Content-Disposition'] = 'attachment; ' + filename_header
        if remove_file:
            os.unlink(file)

        return response


class GenericViewSet(GenericAPIView, rf_viewsets.GenericViewSet):
    """
    Extends standard viewset features
    """

    search_param = 'search'

    def get_serializer_class(self):
        """
        Return the class to use for the serializer based who requesting and what is being
        requested.

        if `admin` or `staff` is requesting, the `admin_serializer_class` will be used if
        declared in viewset.

        if the object `owner` is requesting, the `owner_[ACTION]_serializer_class` will be used
        if declared in viewset

        Other than these the action based serializer class will be returned.

        For eg: if you want different serializer for create action you can define serializer as
        ``create_serializer_class`` attribute name.
        Default to using `self.serializer_class`.

        You may want to override this if you need to provide different
        serializations depending on the incoming request.
        """

        # Admin serializer
        admin_serializer = self._get_admin_serializer()
        if admin_serializer:
            return admin_serializer

        # Owner classes
        owner_serializer_class = self._get_owner_serializer()
        if owner_serializer_class:
            return owner_serializer_class

        # Action serializer
        serializer_class = getattr(self, '%s_serializer_class' % self.action, None)
        if serializer_class:
            return serializer_class

        return self.serializer_class

    def _get_admin_serializer(self):
        if self.request.user.is_superuser:
            return getattr(self, 'admin_serializer_class', None)

    def _get_owner_serializer(self):
        owner_serializer_class = getattr(self, 'owner_%s_serializer_class' % self.action, None)
        if owner_serializer_class:
            _u = self.request.user
            result = any(_u == getattr(self.object, field) or _u.id == getattr(self.object, field)
                         for field in self.ownership_fields)
            if result is True:
                return owner_serializer_class


class ModelViewSet(rf_viewsets.ModelViewSet, GenericViewSet):
    """
    Base class for model view set
    """
    pass


class NestedViewSetMixin(_NestedViewSetMixin):
    """
    Extends feature to
    * Method to get parent object
    * Add parent query dict to ``request.data``
    """

    def create(self, request, *args, **kwargs):
        self.get_parent_object()

        # Since QueryDict now immutable
        if isinstance(request.data, QueryDict):
            request.data._mutable = True

        request.data.update(**self.get_parents_query_dict())
        request.parent_query_dict = self.get_parents_query_dict()

        return super().create(request, *args, **kwargs)

    def get_parent_object(self):
        """
        Checks the object's parent object permission and returns it
        """
        # Getting related field name
        parent_object_name = list(self.get_parents_query_dict().keys())[:1][0]
        # Getting parent model
        parent_model = self.get_queryset().model._meta.get_field(parent_object_name).related_model
        # Getting parent object
        parent_object = parent_model.objects.get(
            id=self.get_parents_query_dict().get(parent_object_name)
        )

        self.check_object_permissions(self.request, parent_object)

        return parent_object
