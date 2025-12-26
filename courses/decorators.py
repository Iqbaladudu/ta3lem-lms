"""
Decorators and Mixins for Course Access Control
"""

from functools import wraps
from django.shortcuts import redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .models import Course
from .access_service import CourseAccessService


def course_access_required(view_func):
    """
    Decorator to check if user has access to course.
    Course must be passed as 'pk' or 'course_id' in URL kwargs.
    
    Usage:
        @course_access_required
        def my_view(request, pk):
            # course is automatically added to kwargs
            course = kwargs['course']
            ...
    """
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        # Get course ID from kwargs
        course_id = kwargs.get('pk') or kwargs.get('course_id')
        
        if not course_id:
            messages.error(request, 'Course not specified')
            return redirect('course_list')
        
        # Get course object
        course = get_object_or_404(Course, id=course_id)
        
        # Check access
        can_access, reason = CourseAccessService.can_access_course(
            request.user, course
        )
        
        if not can_access:
            # Handle different denial reasons
            if reason == 'subscription_expired':
                messages.warning(
                    request,
                    f'Subscription Anda telah berakhir. '
                    f'Perpanjang untuk melanjutkan akses ke "{course.title}"'
                )
                return redirect('subscriptions:manage')
            
            elif reason == 'not_enrolled':
                messages.info(
                    request,
                    f'Anda belum terdaftar di kursus ini.'
                )
                # Redirect to course detail to show enrollment options
                return redirect('course_detail', slug=course.slug)
            
            elif reason == 'payment_pending':
                messages.warning(
                    request,
                    f'Pembayaran untuk kursus "{course.title}" belum selesai.'
                )
                return redirect('course_detail', slug=course.slug)
            
            else:
                messages.error(
                    request,
                    f'Anda tidak memiliki akses ke kursus "{course.title}"'
                )
                return redirect('course_list')
        
        # Add course to kwargs for view to use
        kwargs['course'] = course
        
        return view_func(request, *args, **kwargs)
    
    return wrapper


class CourseAccessMixin:
    """
    Mixin for class-based views to check course access.
    
    Usage:
        class MyCourseView(CourseAccessMixin, DetailView):
            model = Course
            ...
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user is authenticated
        if not request.user.is_authenticated:
            messages.info(request, 'Silakan login terlebih dahulu')
            return redirect('student_login')
        
        # Get course
        if hasattr(self, 'get_object'):
            course = self.get_object()
        else:
            # Try to get from pk/course_id
            course_id = kwargs.get('pk') or kwargs.get('course_id')
            if course_id:
                course = get_object_or_404(Course, id=course_id)
            else:
                messages.error(request, 'Course not found')
                return redirect('course_list')
        
        # Check access
        can_access, reason = CourseAccessService.can_access_course(
            request.user, course
        )
        
        if not can_access:
            # Handle different denial reasons
            if reason == 'subscription_expired':
                messages.warning(
                    request,
                    f'Subscription Anda telah berakhir. '
                    f'Perpanjang untuk melanjutkan akses ke "{course.title}"'
                )
                return redirect('subscriptions:manage')
            
            elif reason == 'not_enrolled':
                messages.info(request, 'Anda belum terdaftar di kursus ini.')
                return redirect('course_detail', slug=course.slug)
            
            elif reason == 'payment_pending':
                messages.warning(
                    request,
                    f'Pembayaran untuk kursus "{course.title}" belum selesai.'
                )
                return redirect('course_detail', slug=course.slug)
            
            else:
                messages.error(request, 'Anda tidak memiliki akses ke kursus ini')
                return redirect('course_list')
        
        # Store course for template
        self.course = course
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add access info to context
        if hasattr(self, 'course'):
            context['course'] = self.course
            
            # Add access expiry date
            expiry_date = CourseAccessService.get_access_expiry_date(
                self.request.user,
                self.course
            )
            context['access_expiry_date'] = expiry_date
        
        return context
