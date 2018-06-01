"""
Pagination
==========
"""

from rest_framework.pagination import PageNumberPagination as PageNumberPagination_


class PageNumberPagination(PageNumberPagination_):
    """
    Extends standard drf.PageNumberPagination class to enabled page_size param
    """
    page_size_query_param = 'page_size'
    max_page_size = 100


class NoPagination(PageNumberPagination_):
    page_size = None
