"""
Custom permission classes for Ta3lem LMS API.
"""

from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission that allows only object owners to edit.
    Read permissions are allowed for any request.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions only allowed to the owner
        return obj.owner == request.user


class IsOwner(permissions.BasePermission):
    """
    Permission that allows only object owners to access.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check ownership via 'owner' or 'user' field
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'user'):
            return obj.user == request.user
        return False


class IsInstructor(permissions.BasePermission):
    """
    Permission that allows only instructors.
    """
    message = 'Only instructors can perform this action.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'instructor'
        )


class IsStudent(permissions.BasePermission):
    """
    Permission that allows only students.
    """
    message = 'Only students can perform this action.'
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.role == 'student'
        )


class IsStaffOrInstructor(permissions.BasePermission):
    """
    Permission that allows staff members or instructors.
    """
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.is_staff or request.user.role == 'instructor'


class IsCourseOwner(permissions.BasePermission):
    """
    Permission for course owners to manage their courses.
    """
    message = 'You must be the course owner to perform this action.'
    
    def has_object_permission(self, request, view, obj):
        # Works for Course or related objects (Module, Content)
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        elif hasattr(obj, 'course'):
            return obj.course.owner == request.user
        elif hasattr(obj, 'module'):
            return obj.module.course.owner == request.user
        return False


class IsEnrolledStudent(permissions.BasePermission):
    """
    Permission for students enrolled in a course.
    """
    message = 'You must be enrolled in this course to access it.'
    
    def has_object_permission(self, request, view, obj):
        from courses.models import CourseEnrollment
        
        # Get the course from the object
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'module'):
            course = obj.module.course
        else:
            course = obj
        
        # Check enrollment
        return CourseEnrollment.objects.filter(
            student=request.user,
            course=course,
            status__in=['enrolled', 'completed']
        ).exists()


class IsEnrolledOrOwner(permissions.BasePermission):
    """
    Permission for enrolled students or course owner.
    """
    
    def has_object_permission(self, request, view, obj):
        from courses.models import CourseEnrollment
        
        # Get the course
        if hasattr(obj, 'course'):
            course = obj.course
        elif hasattr(obj, 'module'):
            course = obj.module.course
        else:
            course = obj
        
        # Owner check
        if course.owner == request.user:
            return True
        
        # Enrollment check
        return CourseEnrollment.objects.filter(
            student=request.user,
            course=course,
            status__in=['enrolled', 'completed']
        ).exists()


class HasActiveSubscription(permissions.BasePermission):
    """
    Permission that allows only users with active subscription.
    """
    message = 'An active subscription is required to access this resource.'
    
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        return request.user.has_active_subscription()


class ReadOnly(permissions.BasePermission):
    """
    Permission that allows only read operations.
    """
    
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS
