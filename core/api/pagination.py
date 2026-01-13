"""
Custom pagination classes for Ta3lem LMS API.
"""

from rest_framework.pagination import PageNumberPagination, CursorPagination
from rest_framework.response import Response


class StandardResultsSetPagination(PageNumberPagination):
    """
    Standard pagination class for most API endpoints.
    Supports page_size query parameter for flexible pagination.
    """
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100
    
    def get_paginated_response(self, data):
        return Response({
            'count': self.page.paginator.count,
            'total_pages': self.page.paginator.num_pages,
            'current_page': self.page.number,
            'next': self.get_next_link(),
            'previous': self.get_previous_link(),
            'results': data
        })


class LargeResultsSetPagination(PageNumberPagination):
    """
    Pagination for endpoints that return larger datasets.
    """
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class SmallResultsSetPagination(PageNumberPagination):
    """
    Pagination for endpoints that return smaller datasets.
    """
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class CourseCursorPagination(CursorPagination):
    """
    Cursor-based pagination for courses listing.
    More efficient for large datasets and prevents issues with concurrent changes.
    """
    page_size = 20
    ordering = '-created'
    cursor_query_param = 'cursor'
