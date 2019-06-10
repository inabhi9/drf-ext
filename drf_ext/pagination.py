"""
Pagination
==========
"""

from rest_framework.pagination import PageNumberPagination as PageNumberPagination_


class PageNumberPagination(PageNumberPagination_):
    """
    Extends standard drf.PageNumberPagination class to enabled page_size param.

    if `view.zero_page_size` is True, it'll allow page_size=0 and pagination for the request
    will be disabled.
    """
    page_size_query_param = 'page_size'
    max_page_size = 100

    def paginate_queryset(self, queryset, request, view=None):
        zero_page_size = getattr(view, 'zero_page_size', False)
        actual_page_size = self.get_actual_page_size(request)

        if zero_page_size is True and actual_page_size == 0:
            self.page_size = None

        return super().paginate_queryset(queryset, request, view)

    def get_actual_page_size(self, request):
        if self.page_size_query_param:
            try:
                return int(request.query_params[self.page_size_query_param])
            except (KeyError, ValueError):
                pass

        return self.page_size


class NoPagination(PageNumberPagination_):
    page_size = None
