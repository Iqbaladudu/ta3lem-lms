from django.contrib import admin
from .models import Subject, Course, Module, Text, File, Image, Video, Content, CourseEnrollment, ContentProgress, ModuleProgress, LearningSession

@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['title', 'slug']
    prepopulated_fields = {'slug': ('title',)}

class ModuleInline(admin.StackedInline):
    model = Module

@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'subject', 'created']
    list_filter = ['created', 'subject']
    search_fields = ['title', 'overview']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [ModuleInline]

@admin.register(Text)
class TextAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'created', 'updated']
    list_filter = ['created', 'updated', 'owner']
    search_fields = ['title', 'content']
    readonly_fields = ['created', 'updated']

@admin.register(File)
class FileAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'file', 'created', 'updated']
    list_filter = ['created', 'updated', 'owner']
    search_fields = ['title']
    readonly_fields = ['created', 'updated']

@admin.register(Image)
class ImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'file', 'created', 'updated']
    list_filter = ['created', 'updated', 'owner']
    search_fields = ['title']
    readonly_fields = ['created', 'updated']

@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    list_display = ['title', 'owner', 'url', 'created', 'updated']
    list_filter = ['created', 'updated', 'owner']
    search_fields = ['title', 'url']
    readonly_fields = ['created', 'updated']

@admin.register(Content)
class ContentAdmin(admin.ModelAdmin):
    list_display = ['module', 'content_type', 'item', 'order']
    list_filter = ['content_type', 'module__course']
    search_fields = ['item__title']

@admin.register(CourseEnrollment)
class CourseEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['student', 'course', 'status', 'enrolled_on', 'progress_percentage', 'last_accessed']
    list_filter = ['status', 'enrolled_on', 'course__subject']
    search_fields = ['student__username', 'student__email', 'course__title']
    readonly_fields = ['enrolled_on', 'completed_on', 'progress_percentage']

@admin.register(ContentProgress)
class ContentProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'content', 'is_completed', 'started_at', 'completed_at']
    list_filter = ['is_completed', 'started_at', 'completed_at']
    search_fields = ['enrollment__student__username', 'content__item__title']
    readonly_fields = ['started_at', 'completed_at']

@admin.register(ModuleProgress)
class ModuleProgressAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'module', 'is_completed', 'started_at', 'completed_at']
    list_filter = ['is_completed', 'started_at', 'completed_at']
    search_fields = ['enrollment__student__username', 'module__title']
    readonly_fields = ['started_at', 'completed_at']

@admin.register(LearningSession)
class LearningSessionAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'content', 'started_at', 'ended_at']
    list_filter = ['started_at', 'ended_at']
    search_fields = ['enrollment__student__username', 'content__item__title']
    readonly_fields = ['started_at', 'ended_at']
