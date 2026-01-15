"""
Custom exception handlers for Ta3lem LMS API.
"""

from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.core.exceptions import ValidationError as DjangoValidationError
from django.http import Http404


def custom_exception_handler(exc, context):
    """
    Custom exception handler that provides consistent error responses.
    """
    # Call REST framework's default exception handler first
    response = exception_handler(exc, context)
    
    if response is not None:
        # Customize error response format
        custom_response_data = {
            'success': False,
            'error': {
                'code': response.status_code,
                'message': get_error_message(response.data),
                'details': response.data if isinstance(response.data, dict) else {'detail': response.data}
            }
        }
        response.data = custom_response_data
        
    return response


def get_error_message(data):
    """
    Extract a human-readable error message from response data.
    """
    if isinstance(data, dict):
        if 'detail' in data:
            return str(data['detail'])
        elif 'non_field_errors' in data:
            return str(data['non_field_errors'][0]) if data['non_field_errors'] else 'Validation error'
        else:
            # Get first field error
            for field, errors in data.items():
                if errors:
                    if isinstance(errors, list):
                        return f"{field}: {errors[0]}"
                    return f"{field}: {errors}"
    elif isinstance(data, list):
        return str(data[0]) if data else 'An error occurred'
    return str(data) if data else 'An error occurred'


class APIException(Exception):
    """
    Base exception class for API errors.
    """
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    default_message = 'An unexpected error occurred.'
    
    def __init__(self, message=None, code=None):
        self.message = message or self.default_message
        if code:
            self.status_code = code
        super().__init__(self.message)


class BadRequestException(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_message = 'Bad request.'


class UnauthorizedException(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_message = 'Authentication credentials were not provided.'


class ForbiddenException(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_message = 'You do not have permission to perform this action.'


class NotFoundException(APIException):
    status_code = status.HTTP_404_NOT_FOUND
    default_message = 'Resource not found.'


class ConflictException(APIException):
    status_code = status.HTTP_409_CONFLICT
    default_message = 'Request conflicts with current state.'


class PaymentRequiredException(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_message = 'Payment is required to access this resource.'
