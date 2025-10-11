from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand

from users.constants import STUDENT_GROUP_NAME, INSTRUCTOR_GROUP_NAME, STAFF_GROUP_NAME


class Command(BaseCommand):
    help = 'Setup groups and permissions for LMS roles'

    def handle(self, *args, **options):
        self.stdout.write('Setting up LMS permissions...')

        # Create Groups
        student_group, _ = Group.objects.get_or_create(name=STUDENT_GROUP_NAME)
        instructor_group, _ = Group.objects.get_or_create(name=INSTRUCTOR_GROUP_NAME)
        staff_group, _ = Group.objects.get_or_create(name=STAFF_GROUP_NAME)

        # Setup permissions
        self.setup_student_permissions(student_group)
        self.stdout.write(self.style.SUCCESS('✓ Student permissions configured'))

        self.setup_instructor_permissions(instructor_group)
        self.stdout.write(self.style.SUCCESS('✓ Instructor permissions configured'))

        self.setup_staff_permissions(staff_group)
        self.stdout.write(self.style.SUCCESS('✓ Staff permissions configured'))

        self.stdout.write(self.style.SUCCESS('\n✓ All permissions setup complete!'))

    def get_permissions(self, permission_strings):
        """Get permissions that exist in the database"""
        permissions = []
        for perm_str in permission_strings:
            try:
                app_label, codename = perm_str.split('.')
                perm = Permission.objects.get(
                    content_type__app_label=app_label,
                    codename=codename
                )
                permissions.append(perm)
            except Permission.DoesNotExist:
                self.stdout.write(
                    self.style.WARNING(f'⚠ Permission {perm_str} does not exist - skipping')
                )
            except ValueError:
                self.stdout.write(
                    self.style.ERROR(f'✗ Invalid permission format: {perm_str}')
                )
        return permissions

    def setup_student_permissions(self, group):
        """Students can view courses, modules, and content"""
        permission_strings = [
            # View permissions for courses
            'courses.view_course',
            'courses.view_module',
            'courses.view_content',
            'courses.view_subject',
            'courses.view_text',
            'courses.view_file',
            'courses.view_image',
            'courses.view_video',
        ]

        permissions = self.get_permissions(permission_strings)
        group.permissions.set(permissions)
        self.stdout.write('Student permissions:')
        for perm in permissions:
            self.stdout.write(f'  - {perm.content_type.app_label}.{perm.codename}')

    def setup_instructor_permissions(self, group):
        """Instructors can manage courses, modules, and content"""
        permission_strings = [
            # Full CRUD on courses
            'courses.view_course',
            'courses.add_course',
            'courses.change_course',
            'courses.delete_course',

            # Full CRUD on modules
            'courses.view_module',
            'courses.add_module',
            'courses.change_module',
            'courses.delete_module',

            # Full CRUD on content
            'courses.view_content',
            'courses.add_content',
            'courses.change_content',
            'courses.delete_content',

            # Full CRUD on subjects
            'courses.view_subject',
            'courses.add_subject',
            'courses.change_subject',
            'courses.delete_subject',

            # Full CRUD on content types
            'courses.view_text',
            'courses.add_text',
            'courses.change_text',
            'courses.delete_text',

            'courses.view_file',
            'courses.add_file',
            'courses.change_file',
            'courses.delete_file',

            'courses.view_image',
            'courses.add_image',
            'courses.change_image',
            'courses.delete_image',

            'courses.view_video',
            'courses.add_video',
            'courses.change_video',
            'courses.delete_video',

            # Custom
            'users.view_dashboard'
        ]

        permissions = self.get_permissions(permission_strings)
        group.permissions.set(permissions)
        self.stdout.write('Instructor permissions:')
        for perm in permissions:
            self.stdout.write(f'  - {perm.content_type.app_label}.{perm.codename}')

    def setup_staff_permissions(self, group):
        """Staff can manage users and view all courses and content"""
        permission_strings = [
            # View permissions for all courses and content
            'courses.view_course',
            'courses.view_module',
            'courses.view_content',
            'courses.view_subject',
            'courses.view_text',
            'courses.view_file',
            'courses.view_image',
            'courses.view_video',

            # User management permissions
            'users.view_user',
            'users.add_user',
            'users.change_user',
            'users.delete_user',
        ]

        permissions = self.get_permissions(permission_strings)
        group.permissions.set(permissions)
        self.stdout.write('Staff permissions:')
        for perm in permissions:
            self.stdout.write(f'  - {perm.content_type.app_label}.{perm.codename}')
