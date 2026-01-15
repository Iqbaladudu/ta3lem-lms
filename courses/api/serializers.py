"""
Serializers for Courses API.
"""

from django.contrib.contenttypes.models import ContentType
from rest_framework import serializers

from courses.models import (
    Subject, Course, Module, Content, ContentItem,
    Text, Video, Image, File,
    CourseEnrollment, CourseWaitlist,
    ContentProgress, ModuleProgress, LearningSession
)
from users.api.serializers import UserSerializer


class SubjectSerializer(serializers.ModelSerializer):
    """
    Serializer for Subject model.
    """
    courses_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Subject
        fields = ['id', 'title', 'slug', 'courses_count']
        read_only_fields = ['id', 'slug']
    
    def get_courses_count(self, obj):
        return obj.courses.filter(status='published').count()


class SubjectDetailSerializer(SubjectSerializer):
    """
    Detailed serializer for Subject including courses.
    """
    courses = serializers.SerializerMethodField()
    
    class Meta(SubjectSerializer.Meta):
        fields = SubjectSerializer.Meta.fields + ['courses']
    
    def get_courses(self, obj):
        courses = obj.courses.filter(status='published')[:10]
        return CourseListSerializer(courses, many=True, context=self.context).data


# Content Item Serializers
class TextSerializer(serializers.ModelSerializer):
    """Serializer for Text content."""
    content_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Text
        fields = ['id', 'title', 'content', 'content_type', 'created', 'updated']
        read_only_fields = ['id', 'created', 'updated']
    
    def get_content_type(self, obj):
        return 'text'


class VideoSerializer(serializers.ModelSerializer):
    """Serializer for Video content."""
    content_type = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = Video
        fields = [
            'id', 'title', 'url', 'file', 'duration', 'video_platform',
            'transcript', 'captions_enabled', 'auto_play',
            'minimum_watch_percentage', 'content_type', 'thumbnail_url',
            'created', 'updated'
        ]
        read_only_fields = ['id', 'video_platform', 'created', 'updated']
    
    def get_content_type(self, obj):
        return 'video'
    
    def get_thumbnail_url(self, obj):
        return obj.get_thumbnail_url()


class ImageSerializer(serializers.ModelSerializer):
    """Serializer for Image content."""
    content_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Image
        fields = ['id', 'title', 'file', 'content_type', 'created', 'updated']
        read_only_fields = ['id', 'created', 'updated']
    
    def get_content_type(self, obj):
        return 'image'


class FileSerializer(serializers.ModelSerializer):
    """Serializer for File content."""
    content_type = serializers.SerializerMethodField()
    
    class Meta:
        model = File
        fields = ['id', 'title', 'file', 'content_type', 'created', 'updated']
        read_only_fields = ['id', 'created', 'updated']
    
    def get_content_type(self, obj):
        return 'file'


class ContentItemSerializer(serializers.ModelSerializer):
    """
    Serializer for ContentItem with polymorphic item rendering.
    """
    item_data = serializers.SerializerMethodField()
    item_type = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentItem
        fields = ['id', 'order', 'item_type', 'item_data']
        read_only_fields = ['id']
    
    def get_item_type(self, obj):
        return obj.content_type.model
    
    def get_item_data(self, obj):
        item = obj.item
        if item is None:
            return None
        
        serializer_map = {
            'text': TextSerializer,
            'video': VideoSerializer,
            'image': ImageSerializer,
            'file': FileSerializer,
        }
        
        model_name = obj.content_type.model
        serializer_class = serializer_map.get(model_name)
        
        if serializer_class:
            return serializer_class(item, context=self.context).data
        return None


class ContentSerializer(serializers.ModelSerializer):
    """
    Serializer for Content model.
    """
    items = ContentItemSerializer(many=True, read_only=True)
    primary_content_type = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = ['id', 'title', 'order', 'primary_content_type', 'items']
        read_only_fields = ['id', 'order']
    
    def get_primary_content_type(self, obj):
        return obj.get_primary_content_type()


class ContentCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating Content with item.
    """
    item_type = serializers.ChoiceField(
        choices=['text', 'video', 'image', 'file'],
        write_only=True
    )
    item_data = serializers.JSONField(write_only=True)
    
    class Meta:
        model = Content
        fields = ['id', 'title', 'module', 'item_type', 'item_data']
        read_only_fields = ['id']
    
    def create(self, validated_data):
        item_type = validated_data.pop('item_type')
        item_data = validated_data.pop('item_data')
        user = self.context['request'].user
        
        # Create content
        content = Content.objects.create(**validated_data)
        
        # Create item based on type
        model_map = {
            'text': Text,
            'video': Video,
            'image': Image,
            'file': File,
        }
        
        ItemModel = model_map[item_type]
        item = ItemModel.objects.create(owner=user, **item_data)
        
        # Create ContentItem linking
        content_type = ContentType.objects.get_for_model(item)
        ContentItem.objects.create(
            content=content,
            content_type=content_type,
            object_id=item.id
        )
        
        return content


class ModuleSerializer(serializers.ModelSerializer):
    """
    Serializer for Module model.
    """
    contents_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Module
        fields = ['id', 'title', 'description', 'order', 'contents_count']
        read_only_fields = ['id', 'order']
    
    def get_contents_count(self, obj):
        return obj.contents.count()


class ModuleDetailSerializer(ModuleSerializer):
    """
    Detailed serializer for Module including contents.
    """
    contents = ContentSerializer(many=True, read_only=True)
    
    class Meta(ModuleSerializer.Meta):
        fields = ModuleSerializer.Meta.fields + ['contents']


class ModuleCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating modules.
    """
    class Meta:
        model = Module
        fields = ['id', 'course', 'title', 'description']
        read_only_fields = ['id']


class CourseListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for course listings.
    """
    subject = SubjectSerializer(read_only=True)
    owner = UserSerializer(read_only=True)
    modules_count = serializers.SerializerMethodField()
    students_count = serializers.SerializerMethodField()
    formatted_price = serializers.SerializerMethodField()
    
    class Meta:
        model = Course
        fields = [
            'id', 'title', 'slug', 'overview', 'subject', 'owner',
            'is_free', 'price', 'currency', 'pricing_type', 'formatted_price',
            'difficulty_level', 'estimated_hours', 'certificate_enabled',
            'status', 'modules_count', 'students_count', 'created'
        ]
        read_only_fields = ['id', 'slug', 'created']
    
    def get_modules_count(self, obj):
        return obj.modules.count()
    
    def get_students_count(self, obj):
        return obj.get_enrollment_count()
    
    def get_formatted_price(self, obj):
        return obj.get_formatted_price()


class CourseDetailSerializer(CourseListSerializer):
    """
    Detailed serializer for single course view.
    """
    modules = ModuleSerializer(many=True, read_only=True)
    enrollment_status = serializers.SerializerMethodField()
    can_enroll = serializers.SerializerMethodField()
    access_options = serializers.SerializerMethodField()
    
    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + [
            'enrollment_type', 'max_capacity', 'waitlist_enabled',
            'modules', 'enrollment_status', 'can_enroll', 'access_options',
            'published_at'
        ]
    
    def get_enrollment_status(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            enrollment = obj.course_enrollments.filter(student=request.user).first()
            if enrollment:
                return {
                    'is_enrolled': True,
                    'status': enrollment.status,
                    'progress_percentage': float(enrollment.progress_percentage),
                    'enrolled_on': enrollment.enrolled_on,
                }
        return {'is_enrolled': False}
    
    def get_can_enroll(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            can, message = obj.can_enroll(request.user)
            return {'can_enroll': can, 'message': message}
        return {'can_enroll': True, 'message': 'Login required'}
    
    def get_access_options(self, obj):
        request = self.context.get('request')
        user = request.user if request else None
        return obj.get_access_options(user)


class CourseCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating/updating courses.
    """
    class Meta:
        model = Course
        fields = [
            'id', 'subject', 'title', 'slug', 'overview',
            'is_free', 'price', 'currency', 'pricing_type',
            'enrollment_type', 'max_capacity', 'waitlist_enabled',
            'difficulty_level', 'estimated_hours', 'certificate_enabled',
            'status'
        ]
        read_only_fields = ['id']
        extra_kwargs = {
            'slug': {'required': False},
        }
    
    def validate(self, attrs):
        # Validate pricing constraints
        pricing_type = attrs.get('pricing_type', 'free')
        is_free = attrs.get('is_free', True)
        price = attrs.get('price')
        
        if pricing_type in ['one_time', 'both']:
            if is_free:
                raise serializers.ValidationError({
                    'is_free': 'Paid courses cannot be marked as free.'
                })
            if not price or price <= 0:
                raise serializers.ValidationError({
                    'price': 'Price must be greater than 0 for paid courses.'
                })
        
        return attrs


# Enrollment Serializers
class CourseEnrollmentSerializer(serializers.ModelSerializer):
    """
    Serializer for course enrollment.
    """
    course = CourseListSerializer(read_only=True)
    student = UserSerializer(read_only=True)
    
    class Meta:
        model = CourseEnrollment
        fields = [
            'id', 'course', 'student', 'status', 'enrolled_on',
            'completed_on', 'progress_percentage', 'last_accessed',
            'access_type', 'payment_status'
        ]
        read_only_fields = ['id', 'enrolled_on', 'progress_percentage']


class EnrollmentCreateSerializer(serializers.Serializer):
    """
    Serializer for creating enrollment.
    """
    course_id = serializers.IntegerField()
    
    def validate_course_id(self, value):
        try:
            course = Course.objects.get(pk=value, status='published')
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found or not available.")
        
        user = self.context['request'].user
        can_enroll, message = course.can_enroll(user)
        
        if not can_enroll:
            raise serializers.ValidationError(message)
        
        return value


class CourseWaitlistSerializer(serializers.ModelSerializer):
    """
    Serializer for course waitlist.
    """
    position = serializers.SerializerMethodField()
    
    class Meta:
        model = CourseWaitlist
        fields = ['id', 'course', 'student', 'joined_waitlist', 'position']
        read_only_fields = ['id', 'joined_waitlist']
    
    def get_position(self, obj):
        return obj.get_position()


# Progress Serializers
class ContentProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for content progress.
    """
    content = ContentSerializer(read_only=True)
    
    class Meta:
        model = ContentProgress
        fields = [
            'id', 'content', 'started_at', 'completed_at',
            'is_completed', 'view_count', 'time_spent', 'last_viewed'
        ]
        read_only_fields = ['id', 'started_at', 'last_viewed']


class ModuleProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for module progress.
    """
    module = ModuleSerializer(read_only=True)
    contents_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = ModuleProgress
        fields = [
            'id', 'module', 'started_at', 'completed_at',
            'is_completed', 'contents_progress'
        ]
        read_only_fields = ['id', 'started_at']
    
    def get_contents_progress(self, obj):
        enrollment = obj.enrollment
        progress_records = ContentProgress.objects.filter(
            enrollment=enrollment,
            content__module=obj.module
        )
        return ContentProgressSerializer(progress_records, many=True).data


class LearningSessionSerializer(serializers.ModelSerializer):
    """
    Serializer for learning sessions.
    """
    duration = serializers.SerializerMethodField()
    
    class Meta:
        model = LearningSession
        fields = ['id', 'content', 'started_at', 'ended_at', 'duration']
        read_only_fields = ['id', 'started_at']
    
    def get_duration(self, obj):
        if obj.ended_at and obj.started_at:
            return (obj.ended_at - obj.started_at).total_seconds()
        return None


class MarkContentCompleteSerializer(serializers.Serializer):
    """
    Serializer for marking content as complete.
    """
    content_id = serializers.IntegerField()
    
    def validate_content_id(self, value):
        try:
            Content.objects.get(pk=value)
        except Content.DoesNotExist:
            raise serializers.ValidationError("Content not found.")
        return value


class CourseProgressSerializer(serializers.Serializer):
    """
    Serializer for overall course progress.
    """
    course_id = serializers.IntegerField()
    progress_percentage = serializers.DecimalField(max_digits=5, decimal_places=2)
    modules_completed = serializers.IntegerField()
    modules_total = serializers.IntegerField()
    contents_completed = serializers.IntegerField()
    contents_total = serializers.IntegerField()
    status = serializers.CharField()
    last_accessed = serializers.DateTimeField()


class BulkModuleOrderSerializer(serializers.Serializer):
    """
    Serializer for bulk module reordering.
    """
    module_orders = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Dictionary of module_id: order pairs'
    )


class BulkContentOrderSerializer(serializers.Serializer):
    """
    Serializer for bulk content reordering.
    """
    content_orders = serializers.DictField(
        child=serializers.IntegerField(),
        help_text='Dictionary of content_id: order pairs'
    )
