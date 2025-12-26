from django.dispatch import receiver
from payments.signals import payment_completed

from .models import Course


@receiver(payment_completed)
def grant_course_access_on_payment(sender, order, user, **kwargs):
    """
    When payment for a course completes, grant access via on_purchase_completed.
    """
    # Check if the purchased item is a Course
    if not isinstance(order.item, Course):
        return

    course = order.item
    course.on_purchase_completed(user, order)
