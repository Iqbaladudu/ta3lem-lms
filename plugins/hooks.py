"""
Plugin Hooks System

Pre-defined hook points for plugin integration.
Provides decorators and utilities for hook management.
"""
from enum import Enum
from functools import wraps
from typing import Any, Callable, List

from .registry import plugin_registry


class CoreHooks(str, Enum):
    """
    Core hook points for plugin integration.
    
    Plugins can register handlers for these hooks to extend functionality.
    A hook name is a dot-separated string identifying the event.
    """
    
    # === User Lifecycle Hooks ===
    USER_REGISTERED = "user.registered"
    USER_LOGIN = "user.login"
    USER_LOGOUT = "user.logout"
    USER_PROFILE_UPDATE = "user.profile_update"
    USER_ROLE_CHANGED = "user.role_changed"
    
    # === Course Lifecycle Hooks ===
    COURSE_CREATED = "course.created"
    COURSE_UPDATED = "course.updated"
    COURSE_PUBLISHED = "course.published"
    COURSE_ARCHIVED = "course.archived"
    COURSE_DELETED = "course.deleted"
    
    # === Enrollment Hooks ===
    COURSE_ENROLLED = "course.enrolled"
    COURSE_UNENROLLED = "course.unenrolled"
    ENROLLMENT_APPROVED = "enrollment.approved"
    ENROLLMENT_REJECTED = "enrollment.rejected"
    
    # === Learning Progress Hooks ===
    CONTENT_VIEWED = "content.viewed"
    CONTENT_COMPLETED = "content.completed"
    MODULE_COMPLETED = "module.completed"
    COURSE_COMPLETED = "course.completed"
    PROGRESS_UPDATED = "progress.updated"
    
    # === Payment Hooks ===
    PAYMENT_INITIATED = "payment.initiated"
    PAYMENT_PROCESSING = "payment.processing"
    PAYMENT_COMPLETED = "payment.completed"
    PAYMENT_FAILED = "payment.failed"
    PAYMENT_REFUNDED = "payment.refunded"
    
    # === Subscription Hooks ===
    SUBSCRIPTION_CREATED = "subscription.created"
    SUBSCRIPTION_RENEWED = "subscription.renewed"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    SUBSCRIPTION_EXPIRED = "subscription.expired"
    
    # === Template Hooks (for injecting content) ===
    TEMPLATE_HEAD = "template.head"
    TEMPLATE_BODY_START = "template.body_start"
    TEMPLATE_BODY_END = "template.body_end"
    TEMPLATE_SIDEBAR = "template.sidebar"
    TEMPLATE_FOOTER = "template.footer"
    
    # === Page-specific Template Hooks ===
    TEMPLATE_COURSE_DETAIL = "template.course_detail"
    TEMPLATE_COURSE_LIST = "template.course_list"
    TEMPLATE_USER_DASHBOARD = "template.user_dashboard"
    TEMPLATE_INSTRUCTOR_DASHBOARD = "template.instructor_dashboard"
    TEMPLATE_STUDENT_COURSE = "template.student_course"


def hook(hook_name: str, priority: int = 10):
    """
    Decorator to mark a method as a hook handler.
    
    Can be used on PluginBase methods to automatically 
    register them as hook handlers.
    
    Args:
        hook_name: Hook to attach to (use CoreHooks enum or string)
        priority: Lower numbers execute first (default: 10)
        
    Example:
        class MyPlugin(PluginBase):
            @hook(CoreHooks.COURSE_COMPLETED, priority=5)
            def on_course_completed(self, user, course, enrollment):
                # Generate certificate
                pass
    """
    if isinstance(hook_name, CoreHooks):
        hook_name = hook_name.value
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        wrapper._hook_name = hook_name
        wrapper._hook_priority = priority
        return wrapper
    return decorator


def trigger_hook(hook_name: str, *args, **kwargs) -> List[Any]:
    """
    Trigger all registered handlers for a hook.
    
    Args:
        hook_name: Hook to trigger (use CoreHooks enum or string)
        *args, **kwargs: Arguments to pass to handlers
        
    Returns:
        List of non-None results from handlers
        
    Example:
        from plugins.hooks import trigger_hook, CoreHooks
        
        # In your view after enrolling a user:
        trigger_hook(
            CoreHooks.COURSE_ENROLLED,
            user=request.user,
            course=course,
            enrollment=enrollment
        )
    """
    if isinstance(hook_name, CoreHooks):
        hook_name = hook_name.value
    
    return plugin_registry.execute_hook(hook_name, *args, **kwargs)


def trigger_template_hook(hook_name: str, request, context=None) -> str:
    """
    Trigger template hooks and return concatenated HTML.
    
    Useful for injecting plugin content into templates.
    
    Args:
        hook_name: Hook to trigger
        request: Django request object
        context: Optional extra context
        
    Returns:
        Concatenated HTML string from all handlers
        
    Example in template:
        {{ template_hooks.body_end }}
    """
    if isinstance(hook_name, CoreHooks):
        hook_name = hook_name.value
    
    results = plugin_registry.execute_hook(hook_name, request=request, context=context)
    return ''.join(str(r) for r in results if r)


def register_hook(hook_name: str, handler: Callable, priority: int = 10) -> None:
    """
    Programmatically register a hook handler.
    
    Alternative to using the @hook decorator, useful for
    dynamic registration or lambdas.
    
    Args:
        hook_name: Hook to attach to
        handler: Callable to execute
        priority: Lower numbers execute first
        
    Example:
        from plugins.hooks import register_hook, CoreHooks
        
        def my_handler(user, course, **kwargs):
            print(f"{user} completed {course}")
        
        register_hook(CoreHooks.COURSE_COMPLETED, my_handler)
    """
    if isinstance(hook_name, CoreHooks):
        hook_name = hook_name.value
    
    plugin_registry.register_hook(hook_name, handler, priority)
