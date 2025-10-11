from django.contrib.auth.models import Group
from django.db.models.signals import post_save
from django.dispatch import receiver

from .constants import ROLE_TO_GROUP
from .models import User, StudentProfile, InstructorProfile


@receiver(post_save, sender=User)
def create_user_profile_and_group(sender, instance, created, **kwargs):
    """
    Auto-create profile based on role AND assign to group
    """
    if created and instance.role:
        # Create role-specific profile
        if instance.role == 'student':
            StudentProfile.objects.get_or_create(user=instance)
        elif instance.role == 'instructor':
            InstructorProfile.objects.get_or_create(user=instance)

        # Assign to group
        instance.groups.clear()
        group_name = ROLE_TO_GROUP.get(instance.role)
        if group_name:
            group, _ = Group.objects.get_or_create(name=group_name)
            instance.groups.add(group)
