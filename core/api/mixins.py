"""
Mixins for Ta3lem LMS API views.
"""

from rest_framework import status
from rest_framework.response import Response


class OwnerMixin:
    """
    Mixin to automatically filter queryset by owner.
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        if hasattr(queryset.model, 'owner'):
            return queryset.filter(owner=self.request.user)
        return queryset


class UserFilterMixin:
    """
    Mixin to filter queryset by user field.
    """
    user_field = 'user'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(**{self.user_field: self.request.user})


class StudentFilterMixin:
    """
    Mixin to filter queryset by student field.
    """
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(student=self.request.user)


class SuccessResponseMixin:
    """
    Mixin to provide consistent success responses.
    """
    
    def success_response(self, data=None, message=None, status_code=status.HTTP_200_OK):
        response_data = {
            'success': True,
        }
        if message:
            response_data['message'] = message
        if data is not None:
            response_data['data'] = data
        return Response(response_data, status=status_code)
    
    def created_response(self, data=None, message='Resource created successfully.'):
        return self.success_response(data, message, status.HTTP_201_CREATED)
    
    def no_content_response(self):
        return Response(status=status.HTTP_204_NO_CONTENT)


class MultiSerializerMixin:
    """
    Mixin to use different serializers for different actions.
    
    Usage:
        class MyViewSet(MultiSerializerMixin, viewsets.ModelViewSet):
            serializer_class = MySerializer
            serializer_action_classes = {
                'list': MyListSerializer,
                'retrieve': MyDetailSerializer,
                'create': MyCreateSerializer,
            }
    """
    serializer_action_classes = {}
    
    def get_serializer_class(self):
        try:
            return self.serializer_action_classes[self.action]
        except KeyError:
            return super().get_serializer_class()


class PerformCreateMixin:
    """
    Mixin to handle object creation with automatic user assignment.
    """
    
    def perform_create(self, serializer):
        # Try common user field names
        if 'owner' in serializer.fields:
            serializer.save(owner=self.request.user)
        elif 'user' in serializer.fields:
            serializer.save(user=self.request.user)
        elif 'student' in serializer.fields:
            serializer.save(student=self.request.user)
        else:
            serializer.save()


class CacheResponseMixin:
    """
    Mixin to add cache headers to responses.
    """
    cache_timeout = 60 * 5  # 5 minutes
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        # Only cache GET requests
        if request.method == 'GET' and response.status_code == 200:
            response['Cache-Control'] = f'max-age={self.cache_timeout}'
        else:
            response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
            
        return response


class BulkCreateMixin:
    """
    Mixin to allow bulk creation of objects.
    """
    
    def get_serializer(self, *args, **kwargs):
        if isinstance(kwargs.get('data'), list):
            kwargs['many'] = True
        return super().get_serializer(*args, **kwargs)
