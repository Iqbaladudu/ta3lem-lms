from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import User, StudentProfile, InstructorProfile


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active', 'date_joined')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    fieldsets = UserAdmin.fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'avatar', 'bio', 'phone_number', 'date_of_birth', 'address', 'city', 'country',
                       'postal_code', 'timezone', 'language', 'email_notifications')
        }),
    )

    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Additional Info', {
            'fields': ('role', 'avatar', 'bio', 'phone_number', 'date_of_birth', 'address', 'city', 'country',
                       'postal_code', 'timezone', 'language', 'email_notifications')
        }),
    )


@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('user__username', 'user__email')
    readonly_fields = ('created_at', 'updated_at')
