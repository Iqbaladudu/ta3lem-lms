"""
Course Access and Enrollment Services
Handles dual pricing system (subscription vs one-time purchase)
"""

from django.db import transaction
from django.utils import timezone
from typing import Tuple, Dict

from .models import Course, CourseEnrollment


class CourseAccessService:
    """Service to validate and manage course access"""
    
    @staticmethod
    def can_access_course(user, course) -> Tuple[bool, str]:
        """
        Check if user can access a course.
        
        Args:
            user: User object
            course: Course object
            
        Returns:
            Tuple[bool, str]: (can_access, reason)
            
        Reasons:
            - 'free': Course is free
            - 'purchased': User purchased the course
            - 'subscription_active': User has active subscription
            - 'not_enrolled': User not enrolled
            - 'subscription_expired': Subscription expired
            - 'payment_pending': Payment not completed
        """
        # 1. Check if course is free
        if course.pricing_type == 'free':
            return True, 'free'
        
        # 2. Check if user has active enrollment
        enrollment = CourseEnrollment.objects.filter(
            student=user,
            course=course,
            status='enrolled'
        ).first()
        
        if not enrollment:
            return False, 'not_enrolled'
        
        # 3. Check payment status
        if enrollment.payment_status not in ['paid', 'free']:
            return False, 'payment_pending'
        
        # 4. Check access type
        if enrollment.access_type == 'purchased':
            # One-time purchase - lifetime access
            return True, 'purchased'
        
        elif enrollment.access_type == 'subscription':
            # Check if subscription is still active
            if enrollment.subscription:
                if enrollment.subscription.is_active():
                    return True, 'subscription_active'
                else:
                    # Subscription expired - revoke access
                    return False, 'subscription_expired'
            else:
                # Check if user has any active subscription
                from subscriptions.services import SubscriptionService
                has_active = SubscriptionService.user_has_active_subscription(user)
                if has_active:
                    return True, 'subscription_active'
                else:
                    return False, 'subscription_expired'
        
        elif enrollment.access_type == 'free':
            return True, 'free'
        
        return False, 'unknown'
    
    @staticmethod
    def get_enrollment_options(user, course) -> Dict[str, bool]:
        """
        Get available enrollment options for a course.
        
        Args:
            user: User object
            course: Course object
            
        Returns:
            dict: {
                'can_enroll_free': bool,
                'can_purchase': bool,
                'can_use_subscription': bool,
                'requires_subscription': bool,
                'already_enrolled': bool,
                'has_access': bool,
            }
        """
        options = {
            'can_enroll_free': False,
            'can_purchase': False,
            'can_use_subscription': False,
            'requires_subscription': False,
            'already_enrolled': False,
            'has_access': False,
        }
        
        # Check if already enrolled
        has_access, reason = CourseAccessService.can_access_course(user, course)
        options['has_access'] = has_access
        
        if has_access:
            options['already_enrolled'] = True
            return options
        
        # Check enrollment options based on pricing_type
        if course.pricing_type == 'free':
            options['can_enroll_free'] = True
        
        elif course.pricing_type == 'one_time':
            options['can_purchase'] = True
        
        elif course.pricing_type == 'subscription_only':
            options['requires_subscription'] = True
            options['can_use_subscription'] = True
        
        elif course.pricing_type == 'both':
            options['can_purchase'] = True
            options['can_use_subscription'] = True
        
        return options
    
    @staticmethod
    def get_access_expiry_date(user, course):
        """
        Get when user's access to course will expire (if applicable).
        
        Returns:
            datetime or None: Expiry date, or None for lifetime access
        """
        enrollment = CourseEnrollment.objects.filter(
            student=user,
            course=course,
            status='enrolled'
        ).first()
        
        if not enrollment:
            return None
        
        if enrollment.access_type == 'purchased':
            # Lifetime access - no expiry
            return None
        
        elif enrollment.access_type == 'subscription':
            if enrollment.subscription:
                return enrollment.subscription.current_period_end
            return None
        
        return None


class EnrollmentService:
    """Handle course enrollment logic for dual pricing system"""
    
    @classmethod
    @transaction.atomic
    def enroll_free(cls, user, course):
        """Enroll user in free course"""
        if course.pricing_type != 'free':
            raise ValueError("Course is not free")
        
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={
                'access_type': 'free',
                'status': 'enrolled',
                'payment_status': 'free',
            }
        )
        
        return enrollment
    
    @classmethod
    @transaction.atomic
    def enroll_with_subscription(cls, user, course, subscription):
        """
        Enroll user via subscription.
        
        Args:
            user: User object
            course: Course object
            subscription: UserSubscription object
        """
        if course.pricing_type not in ['subscription_only', 'both']:
            raise ValueError("Course does not support subscription access")
        
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={
                'access_type': 'subscription',
                'subscription': subscription,
                'status': 'enrolled',
                'payment_status': 'paid',
            }
        )
        
        if not created:
            # Update existing enrollment to subscription
            if enrollment.access_type != 'purchased':  # Don't downgrade purchased access
                enrollment.access_type = 'subscription'
                enrollment.subscription = subscription
                enrollment.status = 'enrolled'
                enrollment.payment_status = 'paid'
                enrollment.save()
        
        return enrollment
    
    @classmethod
    @transaction.atomic
    def enroll_with_purchase(cls, user, course, order):
        """
        Enroll user via one-time purchase.
        
        Args:
            user: User object
            course: Course object
            order: Order object
        """
        if course.pricing_type not in ['one_time', 'both']:
            raise ValueError("Course does not support one-time purchase")
        
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=user,
            course=course,
            defaults={
                'access_type': 'purchased',
                'order': order,
                'status': 'enrolled',
                'payment_status': 'paid',
                'payment_amount': order.total_amount,
                'payment_date': order.completed_at,
            }
        )
        
        if not created and enrollment.access_type == 'subscription':
            # Upgrade from subscription to purchased (lifetime access)
            enrollment.access_type = 'purchased'
            enrollment.order = order
            enrollment.payment_amount = order.total_amount
            enrollment.payment_date = order.completed_at
            enrollment.save()
        
        return enrollment
    
    @classmethod
    @transaction.atomic
    def revoke_subscription_access(cls, user, subscription=None):
        """
        Revoke access to courses when subscription expires.
        Only affects subscription-based enrollments.
        
        Args:
            user: User object
            subscription: UserSubscription object (optional, all if None)
            
        Returns:
            int: Number of enrollments affected
        """
        query = CourseEnrollment.objects.filter(
            student=user,
            access_type='subscription',
            status='enrolled'
        )
        
        if subscription:
            query = query.filter(subscription=subscription)
        
        # Mark as paused (not withdrawn, so progress is kept)
        count = query.update(status='paused')
        
        return count
    
    @classmethod
    @transaction.atomic
    def restore_subscription_access(cls, user, subscription):
        """
        Restore access when subscription is renewed.
        
        Args:
            user: User object
            subscription: UserSubscription object
            
        Returns:
            int: Number of enrollments restored
        """
        enrollments = CourseEnrollment.objects.filter(
            student=user,
            access_type='subscription',
            subscription=subscription,
            status='paused'
        )
        
        count = enrollments.update(status='enrolled')
        
        return count
    
    @classmethod
    def get_user_courses(cls, user, access_type=None):
        """
        Get courses user has access to, optionally filtered by access type.
        
        Args:
            user: User object
            access_type: Optional filter ('free', 'purchased', 'subscription')
            
        Returns:
            QuerySet: CourseEnrollment objects
        """
        query = CourseEnrollment.objects.filter(
            student=user,
            status='enrolled'
        ).select_related('course', 'subscription', 'order')
        
        if access_type:
            query = query.filter(access_type=access_type)
        
        return query
