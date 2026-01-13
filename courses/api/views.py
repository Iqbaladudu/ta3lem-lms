"""
API Views for Courses app.
"""

from django.db.models import Count, Avg
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from django_filters import rest_framework as filters
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter

from core.api import (
    StandardResultsSetPagination, LargeResultsSetPagination,
    IsOwnerOrReadOnly, IsInstructor, IsCourseOwner, IsEnrolledOrOwner,
    OwnerMixin, SuccessResponseMixin, MultiSerializerMixin
)
from courses.models import (
    Subject, Course, Module, Content, ContentItem,
    CourseEnrollment, CourseWaitlist,
    ContentProgress, ModuleProgress, LearningSession
)
from .serializers import (
    SubjectSerializer, SubjectDetailSerializer,
    CourseListSerializer, CourseDetailSerializer, CourseCreateSerializer,
    ModuleSerializer, ModuleDetailSerializer, ModuleCreateSerializer,
    ContentSerializer, ContentCreateSerializer, ContentItemSerializer,
    CourseEnrollmentSerializer, EnrollmentCreateSerializer,
    CourseWaitlistSerializer,
    ContentProgressSerializer, ModuleProgressSerializer,
    LearningSessionSerializer, MarkContentCompleteSerializer,
    CourseProgressSerializer,
    BulkModuleOrderSerializer, BulkContentOrderSerializer,
)


# Filters
class CourseFilter(filters.FilterSet):
    """
    FilterSet for Course model.
    """
    min_price = filters.NumberFilter(field_name='price', lookup_expr='gte')
    max_price = filters.NumberFilter(field_name='price', lookup_expr='lte')
    is_free = filters.BooleanFilter()
    subject = filters.CharFilter(field_name='subject__slug')
    difficulty = filters.ChoiceFilter(
        field_name='difficulty_level',
        choices=[('beginner', 'Beginner'), ('intermediate', 'Intermediate'), ('advanced', 'Advanced')]
    )
    
    class Meta:
        model = Course
        fields = ['is_free', 'subject', 'pricing_type', 'difficulty_level', 'certificate_enabled']


# ViewSets
@extend_schema_view(
    list=extend_schema(tags=['Courses'], summary='List subjects'),
    retrieve=extend_schema(tags=['Courses'], summary='Get subject details'),
)
class SubjectViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for listing and retrieving subjects.
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [AllowAny]
    pagination_class = StandardResultsSetPagination
    lookup_field = 'slug'
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return SubjectDetailSerializer
        return SubjectSerializer


@extend_schema_view(
    list=extend_schema(
        tags=['Courses'],
        summary='List courses',
        description='List all published courses with optional filtering.',
        parameters=[
            OpenApiParameter(name='subject', description='Filter by subject slug'),
            OpenApiParameter(name='difficulty', description='Filter by difficulty level'),
            OpenApiParameter(name='is_free', description='Filter free courses'),
            OpenApiParameter(name='search', description='Search in title and overview'),
        ]
    ),
    retrieve=extend_schema(
        tags=['Courses'],
        summary='Get course details',
        description='Get detailed information about a specific course.'
    ),
    create=extend_schema(
        tags=['Courses'],
        summary='Create course',
        description='Create a new course. Instructor only.'
    ),
    update=extend_schema(
        tags=['Courses'],
        summary='Update course',
        description='Update course details. Owner only.'
    ),
    partial_update=extend_schema(
        tags=['Courses'],
        summary='Partial update course',
        description='Partially update course details. Owner only.'
    ),
    destroy=extend_schema(
        tags=['Courses'],
        summary='Delete course',
        description='Delete a course. Owner only.'
    ),
)
class CourseViewSet(MultiSerializerMixin, OwnerMixin, viewsets.ModelViewSet):
    """
    ViewSet for Course CRUD operations.
    """
    queryset = Course.objects.all()
    serializer_class = CourseListSerializer
    serializer_action_classes = {
        'list': CourseListSerializer,
        'retrieve': CourseDetailSerializer,
        'create': CourseCreateSerializer,
        'update': CourseCreateSerializer,
        'partial_update': CourseCreateSerializer,
    }
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = LargeResultsSetPagination
    filterset_class = CourseFilter
    search_fields = ['title', 'overview']
    ordering_fields = ['created', 'title', 'price']
    ordering = ['-created']
    lookup_field = 'slug'
    
    def get_queryset(self):
        queryset = Course.objects.all()
        
        # Annotate with counts
        queryset = queryset.annotate(
            total_modules=Count('modules'),
            total_students=Count('students')
        )
        
        # For list action, show only published courses to non-owners
        if self.action == 'list':
            if self.request.user.is_authenticated:
                # Show published + own courses for authenticated users
                # Using Q objects for better query optimization
                from django.db.models import Q
                queryset = queryset.filter(
                    Q(status='published') | Q(owner=self.request.user)
                )
            else:
                queryset = queryset.filter(status='published')
        
        return queryset.select_related('subject', 'owner')
    
    def get_permissions(self):
        if self.action in ['create']:
            return [IsAuthenticated(), IsInstructor()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsCourseOwner()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    @extend_schema(
        tags=['Courses'],
        summary='Get my courses',
        description='Get courses created by the current user.'
    )
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated, IsInstructor])
    def my_courses(self, request):
        """
        List courses owned by the current instructor.
        """
        queryset = self.get_queryset().filter(owner=request.user)
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = CourseListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        serializer = CourseListSerializer(queryset, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Courses'],
        summary='Get course modules',
        description='Get all modules for a specific course.'
    )
    @action(detail=True, methods=['get'])
    def modules(self, request, slug=None):
        """
        Get all modules for a course.
        """
        course = self.get_object()
        modules = course.modules.all()
        serializer = ModuleDetailSerializer(modules, many=True, context={'request': request})
        return Response(serializer.data)
    
    @extend_schema(
        tags=['Courses'],
        summary='Get course statistics',
        description='Get enrollment and progress statistics for a course. Owner only.'
    )
    @action(detail=True, methods=['get'], permission_classes=[IsAuthenticated, IsCourseOwner])
    def statistics(self, request, slug=None):
        """
        Get course statistics for instructors.
        """
        course = self.get_object()
        
        enrollments = CourseEnrollment.objects.filter(course=course)
        
        stats = {
            'total_students': enrollments.count(),
            'active_students': enrollments.filter(status='enrolled').count(),
            'completed_students': enrollments.filter(status='completed').count(),
            'average_progress': enrollments.aggregate(avg=Avg('progress_percentage'))['avg'] or 0,
            'total_modules': course.modules.count(),
            'total_contents': Content.objects.filter(module__course=course).count(),
        }
        
        return Response(stats)
    
    @extend_schema(
        tags=['Courses'],
        summary='Publish course',
        description='Publish a draft course. Owner only.'
    )
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, IsCourseOwner])
    def publish(self, request, slug=None):
        """
        Publish a course.
        """
        course = self.get_object()
        
        if course.status == 'published':
            return Response(
                {'detail': 'Course is already published.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        course.status = 'published'
        course.published_at = timezone.now()
        course.save()
        
        return Response({
            'success': True,
            'message': 'Course published successfully.',
            'data': CourseDetailSerializer(course, context={'request': request}).data
        })


@extend_schema_view(
    list=extend_schema(tags=['Courses'], summary='List modules'),
    retrieve=extend_schema(tags=['Courses'], summary='Get module details'),
    create=extend_schema(tags=['Courses'], summary='Create module'),
    update=extend_schema(tags=['Courses'], summary='Update module'),
    destroy=extend_schema(tags=['Courses'], summary='Delete module'),
)
class ModuleViewSet(MultiSerializerMixin, viewsets.ModelViewSet):
    """
    ViewSet for Module CRUD operations.
    """
    queryset = Module.objects.all()
    serializer_class = ModuleSerializer
    serializer_action_classes = {
        'retrieve': ModuleDetailSerializer,
        'create': ModuleCreateSerializer,
        'update': ModuleCreateSerializer,
    }
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        course_slug = self.kwargs.get('course_slug')
        if course_slug:
            return Module.objects.filter(course__slug=course_slug).select_related('course')
        return Module.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsCourseOwner()]
        return super().get_permissions()
    
    @extend_schema(
        tags=['Courses'],
        summary='Reorder modules',
        description='Bulk reorder modules within a course.'
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def reorder(self, request):
        """
        Bulk reorder modules.
        """
        serializer = BulkModuleOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        orders = serializer.validated_data['module_orders']
        for module_id, order in orders.items():
            Module.objects.filter(
                id=int(module_id),
                course__owner=request.user
            ).update(order=order)
        
        return Response({'success': True, 'message': 'Modules reordered successfully.'})


@extend_schema_view(
    list=extend_schema(tags=['Courses'], summary='List contents'),
    retrieve=extend_schema(tags=['Courses'], summary='Get content details'),
    create=extend_schema(tags=['Courses'], summary='Create content'),
    destroy=extend_schema(tags=['Courses'], summary='Delete content'),
)
class ContentViewSet(MultiSerializerMixin, viewsets.ModelViewSet):
    """
    ViewSet for Content CRUD operations.
    """
    queryset = Content.objects.all()
    serializer_class = ContentSerializer
    serializer_action_classes = {
        'create': ContentCreateSerializer,
    }
    permission_classes = [IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        module_id = self.kwargs.get('module_id')
        if module_id:
            return Content.objects.filter(module_id=module_id).prefetch_related('items')
        return Content.objects.all()
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsAuthenticated()]
        return super().get_permissions()
    
    @extend_schema(
        tags=['Courses'],
        summary='Reorder contents',
        description='Bulk reorder contents within a module.'
    )
    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def reorder(self, request):
        """
        Bulk reorder contents.
        """
        serializer = BulkContentOrderSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        orders = serializer.validated_data['content_orders']
        for content_id, order in orders.items():
            Content.objects.filter(
                id=int(content_id),
                module__course__owner=request.user
            ).update(order=order)
        
        return Response({'success': True, 'message': 'Contents reordered successfully.'})


# Enrollment Views
@extend_schema_view(
    list=extend_schema(
        tags=['Enrollments'],
        summary='List my enrollments',
        description='List all course enrollments for the current user.'
    ),
    retrieve=extend_schema(
        tags=['Enrollments'],
        summary='Get enrollment details',
        description='Get details of a specific enrollment.'
    ),
)
class EnrollmentViewSet(SuccessResponseMixin, viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for managing course enrollments.
    """
    queryset = CourseEnrollment.objects.all()
    serializer_class = CourseEnrollmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    filterset_fields = ['status', 'payment_status']
    
    def get_queryset(self):
        return CourseEnrollment.objects.filter(
            student=self.request.user
        ).select_related('course', 'course__subject')
    
    @extend_schema(
        tags=['Enrollments'],
        summary='Enroll in course',
        description='Enroll the current user in a course.'
    )
    @action(detail=False, methods=['post'])
    def enroll(self, request):
        """
        Enroll in a course.
        """
        serializer = EnrollmentCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        
        course_id = serializer.validated_data['course_id']
        course = Course.objects.get(pk=course_id)
        user = request.user
        
        # Handle free course enrollment
        if course.pricing_type == 'free' or course.is_free:
            enrollment_status = 'enrolled' if course.enrollment_type == 'open' else 'pending'
            
            enrollment = CourseEnrollment.objects.create(
                student=user,
                course=course,
                status=enrollment_status,
                payment_status='free',
                access_type='free',
            )
            
            if course.enrollment_type == 'open':
                course.students.add(user)
                # Create initial module progress
                first_module = course.modules.order_by('order').first()
                if first_module:
                    ModuleProgress.objects.create(
                        enrollment=enrollment,
                        module=first_module
                    )
            
            return self.success_response(
                data=CourseEnrollmentSerializer(enrollment).data,
                message='Successfully enrolled in course.',
                status_code=status.HTTP_201_CREATED
            )
        
        # For paid courses, redirect to payment
        from django.urls import reverse
        checkout_url = reverse('api:v1:api_checkout')
        return Response({
            'success': False,
            'message': 'This course requires payment.',
            'payment_required': True,
            'checkout_url': checkout_url,
            'checkout_data': {
                'order_type': 'course',
                'item_id': course.id
            }
        }, status=status.HTTP_402_PAYMENT_REQUIRED)
    
    @extend_schema(
        tags=['Enrollments'],
        summary='Withdraw from course',
        description='Withdraw from an enrolled course.'
    )
    @action(detail=True, methods=['post'])
    def withdraw(self, request, pk=None):
        """
        Withdraw from a course.
        """
        enrollment = self.get_object()
        
        if enrollment.status == 'withdrawn':
            return Response(
                {'detail': 'Already withdrawn from this course.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        enrollment.status = 'withdrawn'
        enrollment.save()
        
        return self.success_response(message='Successfully withdrawn from course.')


# Progress Views
@extend_schema(tags=['Progress'])
class CourseProgressView(SuccessResponseMixin, generics.RetrieveAPIView):
    """
    Get overall progress for a course.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = CourseProgressSerializer
    
    @extend_schema(
        summary='Get course progress',
        description='Get overall progress for an enrolled course.'
    )
    def get(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        enrollment = get_object_or_404(
            CourseEnrollment,
            student=request.user,
            course=course
        )
        
        # Calculate progress
        total_modules = course.modules.count()
        completed_modules = ModuleProgress.objects.filter(
            enrollment=enrollment,
            is_completed=True
        ).count()
        
        total_contents = Content.objects.filter(module__course=course).count()
        completed_contents = ContentProgress.objects.filter(
            enrollment=enrollment,
            is_completed=True
        ).count()
        
        data = {
            'course_id': course.id,
            'progress_percentage': enrollment.progress_percentage,
            'modules_completed': completed_modules,
            'modules_total': total_modules,
            'contents_completed': completed_contents,
            'contents_total': total_contents,
            'status': enrollment.status,
            'last_accessed': enrollment.last_accessed,
        }
        
        return self.success_response(data=data)


@extend_schema(tags=['Progress'])
class MarkContentCompleteView(SuccessResponseMixin, generics.CreateAPIView):
    """
    Mark a content as complete.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = MarkContentCompleteSerializer
    
    @extend_schema(
        summary='Mark content complete',
        description='Mark a specific content as completed.'
    )
    def post(self, request, course_slug):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        content_id = serializer.validated_data['content_id']
        content = get_object_or_404(Content, pk=content_id)
        course = content.module.course
        
        # Verify enrollment
        enrollment = get_object_or_404(
            CourseEnrollment,
            student=request.user,
            course=course,
            status__in=['enrolled', 'completed']
        )
        
        # Get or create content progress
        content_progress, _ = ContentProgress.objects.get_or_create(
            enrollment=enrollment,
            content=content
        )
        
        if not content_progress.is_completed:
            content_progress.mark_completed()
        
        # Update enrollment progress
        enrollment.update_progress()
        
        return self.success_response(
            data={
                'progress_percentage': float(enrollment.progress_percentage),
                'content_completed': content_progress.is_completed,
                'course_completed': enrollment.status == 'completed'
            },
            message='Content marked as complete.'
        )


@extend_schema(tags=['Progress'])
class ModuleProgressView(SuccessResponseMixin, generics.ListAPIView):
    """
    Get progress for all modules in a course.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = ModuleProgressSerializer
    
    @extend_schema(
        summary='Get module progress',
        description='Get progress for all modules in an enrolled course.'
    )
    def get(self, request, course_slug):
        course = get_object_or_404(Course, slug=course_slug)
        enrollment = get_object_or_404(
            CourseEnrollment,
            student=request.user,
            course=course
        )
        
        # Get or create progress for all modules
        modules_progress = []
        for module in course.modules.all():
            progress, _ = ModuleProgress.objects.get_or_create(
                enrollment=enrollment,
                module=module
            )
            modules_progress.append(progress)
        
        serializer = ModuleProgressSerializer(modules_progress, many=True)
        return self.success_response(data=serializer.data)


@extend_schema(tags=['Progress'])
class LearningSessionViewSet(SuccessResponseMixin, viewsets.ModelViewSet):
    """
    ViewSet for managing learning sessions.
    """
    queryset = LearningSession.objects.all()
    serializer_class = LearningSessionSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['get', 'post', 'patch']
    
    def get_queryset(self):
        return LearningSession.objects.filter(
            enrollment__student=self.request.user
        ).order_by('-started_at')
    
    @extend_schema(
        tags=['Progress'],
        summary='Start learning session',
        description='Start a new learning session for a content.'
    )
    def create(self, request, *args, **kwargs):
        content_id = request.data.get('content_id')
        content = get_object_or_404(Content, pk=content_id)
        
        enrollment = get_object_or_404(
            CourseEnrollment,
            student=request.user,
            course=content.module.course,
            status__in=['enrolled', 'completed']
        )
        
        session = LearningSession.objects.create(
            enrollment=enrollment,
            content=content
        )
        
        return self.success_response(
            data=LearningSessionSerializer(session).data,
            message='Learning session started.',
            status_code=status.HTTP_201_CREATED
        )
    
    @extend_schema(
        tags=['Progress'],
        summary='End learning session',
        description='End an active learning session.'
    )
    @action(detail=True, methods=['post'])
    def end(self, request, pk=None):
        session = self.get_object()
        
        if session.ended_at:
            return Response(
                {'detail': 'Session already ended.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        session.end_session()
        
        return self.success_response(
            data=LearningSessionSerializer(session).data,
            message='Learning session ended.'
        )
