"""
Core API package for Ta3lem LMS.
Contains base classes, mixins, permissions, and utilities for the API.
"""

from .pagination import (
    StandardResultsSetPagination,
    LargeResultsSetPagination,
    SmallResultsSetPagination,
    CourseCursorPagination,
)
from .permissions import (
    IsOwnerOrReadOnly,
    IsOwner,
    IsInstructor,
    IsStudent,
    IsStaffOrInstructor,
    IsCourseOwner,
    IsEnrolledStudent,
    IsEnrolledOrOwner,
    HasActiveSubscription,
    ReadOnly,
)
from .mixins import (
    OwnerMixin,
    UserFilterMixin,
    StudentFilterMixin,
    SuccessResponseMixin,
    MultiSerializerMixin,
    PerformCreateMixin,
    CacheResponseMixin,
    BulkCreateMixin,
)
from .exceptions import (
    APIException,
    BadRequestException,
    UnauthorizedException,
    ForbiddenException,
    NotFoundException,
    ConflictException,
    PaymentRequiredException,
)

__all__ = [
    # Pagination
    'StandardResultsSetPagination',
    'LargeResultsSetPagination',
    'SmallResultsSetPagination',
    'CourseCursorPagination',
    # Permissions
    'IsOwnerOrReadOnly',
    'IsOwner',
    'IsInstructor',
    'IsStudent',
    'IsStaffOrInstructor',
    'IsCourseOwner',
    'IsEnrolledStudent',
    'IsEnrolledOrOwner',
    'HasActiveSubscription',
    'ReadOnly',
    # Mixins
    'OwnerMixin',
    'UserFilterMixin',
    'StudentFilterMixin',
    'SuccessResponseMixin',
    'MultiSerializerMixin',
    'PerformCreateMixin',
    'CacheResponseMixin',
    'BulkCreateMixin',
    # Exceptions
    'APIException',
    'BadRequestException',
    'UnauthorizedException',
    'ForbiddenException',
    'NotFoundException',
    'ConflictException',
    'PaymentRequiredException',
]
