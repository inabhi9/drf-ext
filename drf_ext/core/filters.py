"""
=======
Filters
=======
"""
from django.db.models import Q
from django_filters.fields import Lookup
from django_filters.filters import Filter
from rest_framework import filters as rf_filters


class OwnerFilterBackend(rf_filters.BaseFilterBackend):
    """
    Filter class that filters list view to its owner's subset.

    It reads two additional attributes in viewset class.

    :param list,tuple ownership_fields: List of str of model property that specify the ownership \
    of object
    :param bool skip_owner_filter: If True, this filter will be switched off
    """

    def filter_queryset(self, request, queryset, view):
        ownership_fields = getattr(view, 'ownership_fields', False)
        skip_owner_filter = getattr(view, 'skip_owner_filter', False)
        __staff_field__ = '__staff__'
        # Define user, as requested user is either owner or any member
        request_user = request.user

        if view.action != 'list' or not ownership_fields or skip_owner_filter is True:
            return queryset

        if '__staff__' in ownership_fields and (request.user.is_staff or request.user.is_superuser):
            return queryset

        q = Q()
        for field in ownership_fields:
            if field == __staff_field__:
                continue
            q |= Q(**{field: request_user.id})
        queryset = queryset.filter(q)

        return queryset


class ListFilter(Filter):
    """
    Filter class that splits comma separated value into list object
    """

    def filter(self, qs, value):
        if not value:
            return qs
        value = value if value.endswith(',') is False else value[:-1]
        value_list = value.split(',')
        return super(ListFilter, self).filter(qs, Lookup(value_list, 'in'))


class DjangoFilterBackend(rf_filters.DjangoFilterBackend):
    """
    Overridden class to pass request object to filter class
    """

    def filter_queryset(self, request, queryset, view):
        filter_class = self.get_filter_class(view, queryset)

        if filter_class and getattr(filter_class.Meta, 'need_request', False) is True:
            return filter_class(request.query_params, queryset=queryset, request=request).qs

        return super().filter_queryset(request, queryset, view)


class DistanceToPointFilterBackend(rf_filters.BaseFilterBackend):
    """

    This is dependent on `django-earthdistance` module

    Provides a DistanceToPointFilter, which is a subclass of DRF BaseFilterBackend.
     Filters a queryset to only those instances within a certain distance of a given point.

     Provides a DistanceToPointFilter, which is a subclass of DRF BaseFilterBackend.
     Filters a queryset to only those instances within a certain distance of a given point.

    `views.py:`

    .. codeblock:

        from drf_ext.core.filters import DistanceToPointFilterBackend

        class LocationList(ListAPIView):

            queryset = models.Location.objects.all()
            serializer_class = serializers.LocationSerializer
            distance_filter_field = ('latitude', 'longitude')
            filter_backends = (DistanceToPointFilterBackend, )

    We can then filter in the URL, using a distance and a point in (lat, long) format.
    The distance can be given in meters.

    The queryset returned by this filter backend also annotate the distance.

    eg:. /location/?distance=4000&point=-122.4862,37.7694 which is equivalent to filtering within
    4000 meters of the point (-122.4862, 37.7694).
    """

    def filter_queryset(self, request, queryset, view):
        from django_earthdistance.models import EarthDistance, LlToEarth

        distance = request.query_params.get('distance')
        point = request.query_params.get('point')
        distance_filter_fields = getattr(view, 'distance_filter_field', None)
        distance_unit = getattr(view, 'distance_unit', None)

        if (not distance_filter_fields or len(distance_filter_fields) != 2 or
                not point):
            return queryset

        # Validate distance
        try:
            distance = float(distance)
        except (TypeError, ValueError):
            return queryset

        # Validate points
        points = str(point).split(',')
        if len(points) != 2:
            return queryset
        try:
            points = list(map(float, points))
        except (TypeError, ValueError):
            return queryset

        if not hasattr(queryset, 'in_distance'):
            return queryset

        # Convert miles to meters
        if distance_unit == 'mile':
            distance *= 1609.34

        qs = queryset.in_distance(distance, distance_filter_fields, points=points)
        qs = qs.annotate(distance=EarthDistance([
            LlToEarth(points),
            LlToEarth(list(distance_filter_fields))
        ]))

        return qs
