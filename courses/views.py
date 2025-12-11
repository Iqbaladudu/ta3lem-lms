from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from django.apps import apps
from django.contrib import messages  # Added for enrollment messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q, Avg
from django.db.models.aggregates import Count
from django.forms import modelform_factory
from django.http import HttpResponse, JsonResponse, Http404
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from users.forms import CourseEnrollForm
from .forms import ModuleFormSets
from .models import (
    Course, Module, Content, ContentItem, Subject, CourseEnrollment,
    ContentProgress, ModuleProgress, LearningSession, CourseWaitlist
)


class CourseListView(ListView):
    model = Course
    template_name = 'courses/course/list.html'
    paginate_by = 4  # Show 6 courses per page
    context_object_name = 'courses'

    def get_queryset(self):
        subject_slug = self.kwargs.get('subject')
        # Include 'published' in cache key to avoid cache pollution between admin and public views
        cache_key = f"course_list_published_{subject_slug}" if subject_slug else "course_list_published"
        queryset = cache.get(cache_key)
        if queryset is None:
            # SECURITY: Only show published courses to the public
            # This ensures draft and archived courses are not visible to students/public
            queryset = Course.objects.filter(status='published').annotate(total_modules=Count('modules')).order_by(
                '-created')
            if subject_slug:
                subject = get_object_or_404(Subject, slug=subject_slug)
                queryset = queryset.filter(subject=subject)
            cache.set(cache_key, list(queryset), timeout=300)  # cache sebagai list
            return queryset
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get all subjects for sidebar
        subjects = cache.get('all_subjects')
        if not subjects:
            subjects = Subject.objects.annotate(total_courses=Count('courses', filter=Q(courses__status='published')))
            cache.set('all_subjects', subjects)
        context['subjects'] = subjects

        # Get current subject if filtering
        subject_slug = self.kwargs.get('subject')
        if subject_slug:
            context['subject'] = get_object_or_404(Subject, slug=subject_slug)
        else:
            context['subject'] = None

        return context


# @method_decorator(cache_page(60 * 15), name='dispatch')
class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course/detail.html'

    def get_object(self):
        """Override to ensure only published courses are accessible to the public"""
        # SECURITY: Only allow public access to published courses
        # This prevents students from accessing draft or archived courses via direct URLs
        slug = self.kwargs.get('slug')
        return get_object_or_404(Course, slug=slug, status='published')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enroll_form'] = CourseEnrollForm(
            initial={'course': self.object}
        )
        if self.request.user.is_authenticated:
            context['user_enrollment'] = CourseEnrollment.objects.filter(
                course=self.object,
                student=self.request.user
            ).first()
        return context


class ModuleOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Module.objects.filter(id=id, course__owner=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class ContentOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    def post(self, request):
        for id, order in self.request_json.items():
            Content.objects.filter(id=id, module__course__owner=request.user).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class ContentItemOrderView(CsrfExemptMixin, JsonRequestResponseMixin, View):
    """View untuk mengatur urutan ContentItem dalam Content"""

    def post(self, request):
        for id, order in self.request_json.items():
            ContentItem.objects.filter(
                id=id,
                content__module__course__owner=request.user
            ).update(order=order)
        return self.render_json_response({'saved': 'OK'})


class ContentItemCreateView(TemplateResponseMixin, View):
    """View untuk menambah ContentItem baru ke Content yang sudah ada"""
    content = None
    model = None
    template_name = 'courses/manage/content/item_form.html'

    @staticmethod
    def get_model(model_name):
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(app_label='courses', model_name=model_name)
        return None

    @staticmethod
    def get_form(model, *args, **kwargs):
        # Use custom form for Video model
        if model.__name__ == 'Video':
            from .forms import VideoForm
            return VideoForm(*args, **kwargs)

        # Default to auto-generated form for other models
        Form = modelform_factory(model, exclude=['owner', 'order', 'created', 'updated'])
        return Form(*args, **kwargs)

    def dispatch(self, request, content_id, model_name):
        self.content = get_object_or_404(
            Content,
            id=content_id,
            module__course__owner=request.user
        )
        self.model = self.get_model(model_name)
        return super().dispatch(request, content_id, model_name)

    def get(self, request, content_id, model_name):
        form = self.get_form(self.model)
        return self.render_to_response({
            'form': form,
            'content': self.content,
            'model_name': model_name
        })

    def post(self, request, content_id, model_name):
        form = self.get_form(self.model, data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()

            # Buat ContentItem
            from django.contrib.contenttypes.models import ContentType
            content_type = ContentType.objects.get_for_model(obj)
            ContentItem.objects.create(
                content=self.content,
                content_type=content_type,
                object_id=obj.id
            )
            return redirect('module_content_list', self.content.module.id)
        return self.render_to_response({
            'form': form,
            'content': self.content,
            'model_name': model_name
        })


class ContentCreateUpdateView(TemplateResponseMixin, View):
    """View untuk membuat/update Content dan ContentItem"""
    module = None
    content = None  # Content object
    model = None  # Item model (Text, Video, Image, File)
    obj = None  # Item object
    template_name = 'courses/manage/content/form.html'

    @staticmethod
    def get_model(model_name):
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(app_label='courses', model_name=model_name)
        return None

    @staticmethod
    def get_form(model, *args, **kwargs):
        # Use custom form for Video model
        if model.__name__ == 'Video':
            from .forms import VideoForm
            return VideoForm(*args, **kwargs)

        # Default to auto-generated form for other models
        Form = modelform_factory(model, exclude=['owner', 'order', 'created', 'updated'])
        return Form(*args, **kwargs)

    def dispatch(self, request, module_id, model_name, id=None, content_id=None):
        self.module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        self.model = self.get_model(model_name)
        if content_id:
            self.content = get_object_or_404(Content, id=content_id, module=self.module)
        if id:
            self.obj = get_object_or_404(self.model, id=id, owner=request.user)
        return super().dispatch(request, module_id, model_name, id, content_id)

    def get(self, request, module_id, model_name, id=None, content_id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({
            'form': form,
            'object': self.obj,
            'content': self.content,
            'module': self.module
        })

    def post(self, request, module_id, model_name, id=None, content_id=None):
        form = self.get_form(self.model, instance=self.obj, data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                # Jika tidak ada content_id, buat Content baru
                if not self.content:
                    self.content = Content.objects.create(
                        module=self.module,
                        title=obj.title
                    )
                # Buat ContentItem yang menghubungkan Content dengan item
                from django.contrib.contenttypes.models import ContentType
                content_type = ContentType.objects.get_for_model(obj)
                ContentItem.objects.create(
                    content=self.content,
                    content_type=content_type,
                    object_id=obj.id
                )
            return redirect('module_content_list', self.module.id)
        return self.render_to_response({
            'form': form,
            'object': self.obj,
            'content': self.content,
            'module': self.module
        })


class ModuleContentListView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/content_list.html'

    def get(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        return self.render_to_response({'module': module})


class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(Content, id=id, module__course__owner=request.user)
        module = content.module
        # Hapus semua ContentItem dan item terkait
        for content_item in content.items.all():
            if content_item.item:
                content_item.item.delete()
            content_item.delete()
        content.delete()

        if request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={
                    'HX-Trigger': 'contentDeleted',
                    'HX-Reswap': 'outerHTML',
                    'HX-Retarget': f'#content-{id}'
                }
            )

        return redirect('module_content_list', module.id)


class ContentItemDeleteView(View):
    """View untuk menghapus satu ContentItem dari Content"""

    def post(self, request, content_id, item_id):
        content_item = get_object_or_404(
            ContentItem,
            id=item_id,
            content_id=content_id,
            content__module__course__owner=request.user
        )
        content = content_item.content
        module = content.module

        # Hapus item dan ContentItem
        if content_item.item:
            content_item.item.delete()
        content_item.delete()

        if request.headers.get('HX-Request'):
            return HttpResponse(
                status=200,
                headers={
                    'HX-Trigger': 'contentItemDeleted',
                    'HX-Reswap': 'outerHTML',
                    'HX-Retarget': f'#content-item-{item_id}'
                }
            )

        return redirect('module_content_list', module.id)


class CourseModuleUpdateView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/formset.html'
    course = None

    def get_formset(self, data=None):
        return ModuleFormSets(instance=self.course, data=data)

    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        self.course = get_object_or_404(Course, id=pk, owner=self.request.user)
        return super().dispatch(request, *args, **kwargs)

    def get(self, request, *args, **kwargs):
        formset = self.get_formset()
        return self.render_to_response({'course': self.course, 'formset': formset})

    def post(self, request, *args, **kwargs):
        formset = self.get_formset(data=request.POST)
        if formset.is_valid():
            formset.save()  # ✅ CRITICAL: Save the formset data!

            # Handle HTMX requests
            if request.headers.get('HX-Request'):
                # Return updated formset HTML for HTMX swap
                formset = self.get_formset()  # Refresh formset with saved data
                response = self.render_to_response({'course': self.course, 'formset': formset})
                # Add success trigger for client-side handling
                response['HX-Trigger'] = 'modulesUpdated'
                return response

            return redirect('manage_course_list')

        # Return form with errors (works for both regular and HTMX requests)
        return self.render_to_response({'course': self.course, 'formset': formset})


class OwnerMixin:
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(owner=self.request.user)


class OwnerEditMixin:
    def form_valid(self, form):
        form.instance.owner = self.request.user
        return super().form_valid(form)


class OwnerCourseMixin(OwnerMixin, LoginRequiredMixin, PermissionRequiredMixin):
    model = Course
    fields = [
        "subject", "title", "slug", "overview",
        "status", "enrollment_type", "max_capacity", "waitlist_enabled",
        "difficulty_level", "estimated_hours", "certificate_enabled"
    ]
    success_url = reverse_lazy("manage_course_list")


class OwnerCourseEditMixin(OwnerCourseMixin, OwnerEditMixin):
    template_name = "courses/manage/course/form.html"


class ManageCourseListView(OwnerCourseMixin, ListView):
    template_name = "courses/manage/course/list.html"
    permission_required = 'courses.view_course'

    def dispatch(self, request, *args, **kwargs):
        is_authenticated = request.user.is_authenticated

        if not is_authenticated:
            return redirect('instructor_login')

        return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        queryset = super().get_queryset()
        search = self.request.GET.get('search', '')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(overview__icontains=search) |
                Q(subject__title__icontains=search)
            )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        courses = self.get_queryset()

        # Calculate statistics
        total_courses = courses.count()
        total_modules = sum(course.modules.count() for course in courses)
        total_students = sum(course.students.count() for course in courses)
        total_contents = sum(
            sum(module.contents.count() for module in course.modules.all())
            for course in courses
        )

        # Add statistics to context
        context['total_courses'] = total_courses
        context['total_modules'] = total_modules
        context['total_students'] = total_students
        context['total_contents'] = total_contents
        context['search'] = self.request.GET.get('search', '')

        return context


class CourseCreateView(OwnerCourseEditMixin, CreateView):
    permission_required = 'courses.add_course'

    def get_form_class(self):
        from .forms import CourseForm
        return CourseForm


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'

    def get_form_class(self):
        from .forms import CourseForm
        return CourseForm


class CourseDeleteView(OwnerCourseMixin, DeleteView):
    template_name = "courses/manage/course/delete.html"
    permission_required = 'courses.delete_course'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        self.object.delete()

        # Return htmx-friendly response
        if request.headers.get('HX-Request'):
            response = HttpResponse('')
            response['HX-Trigger'] = 'courseDeleted'
            return response

        return redirect(self.success_url)


# ============================================================================
# COURSE TRACKING VIEWS
# ============================================================================

class StudentEnrollCourseView(LoginRequiredMixin, View):
    """Handle student course enrollment with waitlist and approval support"""

    def post(self, request, pk):
        # SECURITY: Only allow enrollment in published courses
        # This prevents students from enrolling in draft or archived courses
        course = get_object_or_404(Course, pk=pk, status='published')
        user = request.user

        # Check if already enrolled
        existing_enrollment = CourseEnrollment.objects.filter(
            student=user,
            course=course
        ).first()

        if existing_enrollment:
            messages.info(request,
                          f'You are already enrolled in "{course.title}" with status: {existing_enrollment.get_status_display()}')
            return redirect('course_detail', slug=course.slug)

        # Check if course allows enrollment
        can_enroll, message = course.can_enroll(user)

        if can_enroll:
            # For paid courses, we need to initiate payment process
            if not course.is_free:
                # TODO: Integrate with payment gateway (Stripe, PayPal, etc.)
                # For now, we'll create enrollment with payment pending status
                enrollment = CourseEnrollment.objects.create(
                    student=user,
                    course=course,
                    status='pending',  # Always pending for paid courses until payment
                    payment_status='pending',
                    payment_amount=course.price
                )

                messages.info(request,
                              f'Untuk menyelesaikan pendaftaran kursus "{course.title}", '
                              f'silakan lakukan pembayaran sebesar {course.get_formatted_price()}. '
                              'Link pembayaran akan dikirim ke email Anda.')
                # Redirect to student dashboard for this course (not public page)
                return redirect('student_course_detail', pk=course.pk)

            # For free courses, proceed with normal enrollment
            enrollment_data = {
                'student': user,
                'course': course,
                'status': 'enrolled' if course.enrollment_type == 'open' else 'pending',
                'payment_status': 'free'
            }

            # Set approval_requested_at for pending enrollments
            if course.enrollment_type in ['approval', 'restricted']:
                enrollment_data['approval_requested_at'] = timezone.now()

            enrollment = CourseEnrollment.objects.create(**enrollment_data)

            if course.enrollment_type == 'open':
                # Add student to course's students M2M field
                course.students.add(user)

                # Create initial module progress for first module
                first_module = course.modules.order_by('order').first()
                if first_module:
                    ModuleProgress.objects.create(
                        enrollment=enrollment,
                        module=first_module
                    )

                messages.success(request, f'Selamat! Anda berhasil mendaftar di kursus "{course.title}" secara gratis!')
                return redirect('student_course_detail', pk=course.pk)
            else:
                # Approval required
                if course.enrollment_type == 'approval':
                    messages.info(request,
                                  f'Permintaan pendaftaran Anda untuk kursus "{course.title}" telah dikirim. '
                                  'Instruktur akan meninjau dan memberikan persetujuan.')
                else:
                    messages.info(request,
                                  f'Permintaan akses Anda untuk kursus terbatas "{course.title}" telah dikirim.')
                return redirect('course_detail', slug=course.slug)

        elif message == "Course full - can join waitlist":
            # Add to waitlist
            waitlist_entry, created = CourseWaitlist.objects.get_or_create(
                course=course,
                student=user
            )

            if created:
                position = waitlist_entry.get_position()
                messages.info(request, f'Course is full. You have been added to the waitlist at position {position}.')
            else:
                position = waitlist_entry.get_position()
                messages.info(request, f'You are already on the waitlist at position {position}.')

            return redirect('course_detail', slug=course.slug)

        else:
            # Cannot enroll
            messages.error(request, f'Cannot enroll: {message}')
            return redirect('course_detail', slug=course.slug)


class StudentJoinWaitlistView(LoginRequiredMixin, View):
    """Handle explicit waitlist joining"""

    def post(self, request, pk):
        # Only allow waitlist joining for published courses
        course = get_object_or_404(Course, pk=pk, status='published')
        user = request.user

        # Check if already enrolled or waitlisted
        if CourseEnrollment.objects.filter(student=user, course=course).exists():
            messages.info(request, 'You are already enrolled in this course.')
            return redirect('course_detail', slug=course.slug)

        if CourseWaitlist.objects.filter(student=user, course=course).exists():
            messages.info(request, 'You are already on the waitlist for this course.')
            return redirect('course_detail', slug=course.slug)

        # Add to waitlist
        waitlist_entry = CourseWaitlist.objects.create(
            course=course,
            student=user
        )

        position = waitlist_entry.get_position()
        messages.success(request, f'You have been added to the waitlist at position {position}.')
        return redirect('course_detail', slug=course.slug)


class ApproveEnrollmentView(LoginRequiredMixin, View):
    """Approve a pending enrollment"""

    def post(self, request, pk):
        enrollment = get_object_or_404(CourseEnrollment, pk=pk)
        course = enrollment.course

        # Check if user is course owner or staff
        if not (request.user == course.owner or request.user.is_staff):
            messages.error(request, 'You do not have permission to approve enrollments.')
            return redirect('course_detail', slug=course.slug)

        if enrollment.status != 'pending':
            messages.error(request, 'Only pending enrollments can be approved.')
            return redirect('instructor_course_analytics', pk=course.pk)

        # Check course capacity
        if course.is_full():
            messages.error(request, 'Cannot approve: course is at capacity.')
            return redirect('instructor_course_analytics', pk=course.pk)

        # Approve enrollment
        enrollment.status = 'enrolled'
        enrollment.approved_by = request.user
        enrollment.approved_at = timezone.now()
        enrollment.save()

        # Add to course students
        course.students.add(enrollment.student)

        # Create initial module progress
        first_module = course.modules.order_by('order').first()
        if first_module:
            ModuleProgress.objects.get_or_create(
                enrollment=enrollment,
                module=first_module
            )

        messages.success(request, f'Approved enrollment for {enrollment.student.get_full_name()}.')
        return redirect('instructor_course_analytics', pk=course.pk)


class RejectEnrollmentView(LoginRequiredMixin, View):
    """Reject a pending enrollment"""

    def post(self, request, pk):
        enrollment = get_object_or_404(CourseEnrollment, pk=pk)
        course = enrollment.course

        # Check if user is course owner or staff
        if not (request.user == course.owner or request.user.is_staff):
            messages.error(request, 'You do not have permission to reject enrollments.')
            return redirect('course_detail', slug=course.slug)

        if enrollment.status != 'pending':
            messages.error(request, 'Only pending enrollments can be rejected.')
            return redirect('instructor_course_analytics', pk=course.pk)

        # Get rejection reason from form
        rejection_reason = request.POST.get('rejection_reason', 'No reason provided')

        # Reject enrollment
        enrollment.status = 'rejected'
        enrollment.approved_by = request.user
        enrollment.approved_at = timezone.now()
        enrollment.rejection_reason = rejection_reason
        enrollment.save()

        messages.success(request, f'Rejected enrollment for {enrollment.student.get_full_name()}.')
        return redirect('instructor_course_analytics', pk=course.pk)


class StudentCourseListView(LoginRequiredMixin, ListView):
    """List all courses enrolled by the student"""
    model = CourseEnrollment
    template_name = 'courses/student/course_list.html'
    context_object_name = 'enrollments'
    paginate_by = 10

    def get_queryset(self):
        queryset = CourseEnrollment.objects.filter(
            student=self.request.user
        ).select_related('course', 'course__subject').order_by('-enrolled_on')

        # Filter by status if provided
        status = self.request.GET.get('status')
        if status and status in dict(CourseEnrollment.STATUS_CHOICES):
            queryset = queryset.filter(status=status)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Add statistics - only count accessible courses
        all_enrollments = CourseEnrollment.objects.filter(student=self.request.user)
        accessible_enrollments = [e for e in all_enrollments if e.can_access_course()]

        context['total_courses'] = all_enrollments.count()
        context['accessible_courses'] = len(accessible_enrollments)
        context['active_courses'] = all_enrollments.filter(status='enrolled').count()
        context['completed_courses'] = all_enrollments.filter(status='completed').count()
        context['avg_progress'] = all_enrollments.aggregate(
            avg=Avg('progress_percentage')
        )['avg'] or 0

        context['status_filter'] = self.request.GET.get('status', '')

        return context


class StudentCourseDetailView(LoginRequiredMixin, DetailView):
    """Display course details and progress for enrolled student"""
    model = Course
    template_name = 'courses/student/course_detail.html'
    context_object_name = 'course'

    def get_object(self):
        """Override to ensure only published courses are accessible to students"""
        # Students can access courses if:
        # 1. Course is published, OR
        # 2. They are already enrolled (even if course becomes draft later)
        pk = self.kwargs.get('pk')
        course = get_object_or_404(Course, pk=pk)

        # Check if user is enrolled in this course
        enrollment = CourseEnrollment.objects.filter(
            student=self.request.user,
            course=course
        ).first()

        # If course is not published and user is not enrolled, deny access
        if course.status != 'published' and not enrollment:
            raise Http404("Course not found or not available.")

        return course

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object

        # Get or create enrollment
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=self.request.user,
            course=course,
            defaults={'status': 'enrolled'}
        )

        if created:
            course.students.add(self.request.user)

        # Check if user can access this course based on enrollment and payment status
        if not enrollment.can_access_course():
            raise Http404("You do not have access to this course. Please check your enrollment and payment status.")

        # Update last accessed
        enrollment.last_accessed = timezone.now()
        enrollment.save(update_fields=['last_accessed'])

        context['enrollment'] = enrollment

        # Get modules with progress
        modules = course.modules.prefetch_related('contents').all()
        modules_data = []

        # Get all content progress for this enrollment at once (optimization)
        all_content_progress = {
            cp.content_id: cp
            for cp in ContentProgress.objects.filter(
                enrollment=enrollment
            ).select_related('content')
        }

        # Collect all contents with their completion status
        all_contents_data = []

        for module in modules:
            module_progress = ModuleProgress.objects.filter(
                enrollment=enrollment,
                module=module
            ).first()

            # Get content progress for this module
            total_contents = module.contents.count()
            completed_contents = 0

            for content in module.contents.all():
                content_progress = all_content_progress.get(content.id)
                is_completed = content_progress.is_completed if content_progress else False
                if is_completed:
                    completed_contents += 1

                all_contents_data.append({
                    'content': content,
                    'progress': content_progress,
                    'is_completed': is_completed
                })

            modules_data.append({
                'module': module,
                'progress': module_progress if module_progress else type('obj', (object,), {'is_completed': False})(),
                'total_contents': total_contents,
                'completed_contents': completed_contents,
                'completion_percentage': (completed_contents / total_contents * 100) if total_contents > 0 else 0,
                'first_content': module.contents.first()  # Add first content for direct navigation
            })

        context['modules_data'] = modules_data
        context['contents_data'] = all_contents_data

        current_module = enrollment.get_current_module()
        context['current_module'] = current_module

        # Add first content of current module for direct link
        if current_module:
            context['current_module_first_content'] = current_module.contents.first()

        return context


class StudentModuleDetailView(LoginRequiredMixin, DetailView):
    """Display module contents and track progress"""
    model = Module
    template_name = 'courses/student/module_detail.html'
    context_object_name = 'module'
    pk_url_kwarg = 'module_pk'

    def get_queryset(self):
        return Module.objects.filter(
            course__pk=self.kwargs['pk']
        ).prefetch_related('contents')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        module = self.object
        course = module.course

        # Get enrollment
        enrollment = get_object_or_404(
            CourseEnrollment,
            student=self.request.user,
            course=course
        )

        # Check if user can access this course
        if not enrollment.can_access_course():
            raise Http404("You do not have access to this course. Please check your enrollment and payment status.")

        # Get or create module progress
        module_progress, created = ModuleProgress.objects.get_or_create(
            enrollment=enrollment,
            module=module
        )

        # Get content progress
        contents_data = []
        completed_count = 0
        for content in module.contents.all():
            content_progress = ContentProgress.objects.filter(
                enrollment=enrollment,
                content=content
            ).first()

            is_completed = content_progress.is_completed if content_progress else False
            if is_completed:
                completed_count += 1

            contents_data.append({
                'content': content,
                'progress': content_progress,
                'is_completed': is_completed
            })

        # Add counts to module_progress for template
        module_progress.completed_contents_count = completed_count
        module_progress.total_contents_count = len(contents_data)

        context['enrollment'] = enrollment
        context['module_progress'] = module_progress
        context['contents_data'] = contents_data
        context['course'] = course
        context['previous_module'] = module.get_previous_in_order()
        context['next_module'] = module.get_next_in_order()

        return context


class StudentContentView(LoginRequiredMixin, DetailView):
    """Display content and track learning progress"""
    model = Content
    template_name = 'courses/student/content_detail.html'
    context_object_name = 'content'
    pk_url_kwarg = 'content_pk'

    def get_queryset(self):
        # Only allow access to content from published courses OR courses user is enrolled in
        course_pk = self.kwargs['pk']
        course = get_object_or_404(Course, pk=course_pk)

        # Check if user is enrolled in this course
        is_enrolled = CourseEnrollment.objects.filter(
            student=self.request.user,
            course=course
        ).exists()

        # If course is not published and user is not enrolled, deny access
        if course.status != 'published' and not is_enrolled:
            raise Http404("Course content not found or not available.")

        return Content.objects.filter(
            module__pk=self.kwargs['module_pk'],
            module__course__pk=self.kwargs['pk']
        ).select_related('module', 'module__course')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        content = self.object
        module = content.module
        course = module.course

        # Get enrollment
        enrollment = get_object_or_404(
            CourseEnrollment,
            student=self.request.user,
            course=course
        )

        # Check if user can access this course
        if not enrollment.can_access_course():
            raise Http404(
                "You do not have access to this course content. Please check your enrollment and payment status.")

        # Get or create content progress
        content_progress, created = ContentProgress.objects.get_or_create(
            enrollment=enrollment,
            content=content
        )

        # Start a learning session
        learning_session = LearningSession.objects.create(
            enrollment=enrollment,
            content=content
        )

        # Get neighboring content (within current module)
        all_contents = list(module.contents.all())
        current_index = next(
            (i for i, c in enumerate(all_contents) if c.id == content.id),
            None
        )

        previous_content = all_contents[current_index - 1] if current_index and current_index > 0 else None
        next_content = all_contents[current_index + 1] if current_index is not None and current_index < len(
            all_contents) - 1 else None

        # If no next content in current module, get first content of next module
        if not next_content:
            next_module = course.modules.filter(order__gt=module.order).first()
            if next_module:
                next_content = next_module.contents.first()
                next_module_context = next_module
            else:
                next_module_context = None
        else:
            next_module_context = None

        # Get all modules with contents and progress for sidebar
        modules_data = []
        all_content_ids = []

        for mod in course.modules.all().prefetch_related('contents'):
            module_progress, _ = ModuleProgress.objects.get_or_create(
                enrollment=enrollment,
                module=mod
            )

            contents_with_progress = []
            completed_count = 0
            total_count = mod.contents.count()

            for cont in mod.contents.all():
                cont_progress = ContentProgress.objects.filter(
                    enrollment=enrollment,
                    content=cont
                ).first()

                is_completed = cont_progress.is_completed if cont_progress else False
                if is_completed:
                    completed_count += 1

                contents_with_progress.append({
                    'content': cont,
                    'is_completed': is_completed
                })
                all_content_ids.append(cont.pk)

            completion_percentage = (completed_count / total_count * 100) if total_count > 0 else 0

            modules_data.append({
                'module': mod,
                'progress': module_progress,
                'contents_with_progress': contents_with_progress,
                'completed_contents': completed_count,
                'total_contents': total_count,
                'completion_percentage': completion_percentage
            })

        # Get all contents data for quick lookup
        contents_data = []
        for content_id in all_content_ids:
            cont_prog = ContentProgress.objects.filter(
                enrollment=enrollment,
                content_id=content_id
            ).first()
            contents_data.append({
                'content_id': content_id,
                'is_completed': cont_prog.is_completed if cont_prog else False
            })

        context['enrollment'] = enrollment
        context['content_progress'] = content_progress
        context['learning_session'] = learning_session
        context['module'] = module
        context['course'] = course
        context['previous_content'] = previous_content
        context['next_content'] = next_content
        context['next_module'] = next_module_context
        context['modules_data'] = modules_data
        context['contents_data'] = contents_data

        return context


class MarkContentCompleteView(LoginRequiredMixin, View):
    """Mark content as completed"""

    def post(self, request, pk, module_pk, content_pk):
        course = get_object_or_404(Course, pk=pk)
        module = get_object_or_404(Module, pk=module_pk, course=course)
        content = get_object_or_404(Content, pk=content_pk, module=module)

        # Get enrollment
        enrollment = get_object_or_404(
            CourseEnrollment,
            student=request.user,
            course=course
        )

        # Get or create content progress and mark as completed
        content_progress, created = ContentProgress.objects.get_or_create(
            enrollment=enrollment,
            content=content
        )

        content_progress.mark_completed()

        # End any active learning sessions for this content
        active_sessions = LearningSession.objects.filter(
            enrollment=enrollment,
            content=content,
            ended_at__isnull=True
        )
        for session in active_sessions:
            session.end_session()

        # Check if module is completed and update
        module_progress, _ = ModuleProgress.objects.get_or_create(
            enrollment=enrollment,
            module=module
        )

        if module_progress.calculate_completion():
            module_progress.mark_completed()

        # Always update course progress after marking content complete
        enrollment.update_progress()

        # Return JSON response for AJAX requests
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.headers.get('HX-Request'):
            return JsonResponse({
                'success': True,
                'progress_percentage': enrollment.progress_percentage,
                'module_completed': module_progress.is_completed,
                'course_completed': enrollment.status == 'completed'
            })

        # Redirect to next content or module
        next_content = module.contents.filter(order__gt=content.order).first()
        if next_content:
            return redirect('student_content_view', pk=pk, module_pk=module_pk, content_pk=next_content.pk)
        else:
            # Go to next module or course detail
            next_module = module.get_next_in_order()
            if next_module:
                return redirect('student_module_detail', pk=pk, module_pk=next_module.pk)
            else:
                return redirect('student_course_detail', pk=pk)


class StudentDashboardView(LoginRequiredMixin, TemplateResponseMixin, View):
    """Student dashboard showing overall progress and statistics"""
    template_name = 'courses/student/dashboard.html'

    def get(self, request):
        user = request.user

        # Get all enrollments
        enrollments = CourseEnrollment.objects.filter(
            student=user
        ).select_related('course', 'course__subject').order_by('-last_accessed')

        # Calculate statistics
        total_courses = enrollments.count()
        active_enrollments = enrollments.filter(status='enrolled')
        completed_courses = enrollments.filter(status='completed').count()

        # Calculate average progress
        avg_progress = enrollments.aggregate(avg=Avg('progress_percentage'))['avg'] or 0

        # Get recent learning sessions
        recent_sessions = LearningSession.objects.filter(
            enrollment__student=user
        ).select_related(
            'enrollment__course', 'content__module'
        ).order_by('-started_at')[:10]

        # Get courses in progress (recently accessed)
        in_progress = active_enrollments.filter(
            last_accessed__isnull=False
        ).order_by('-last_accessed')[:5]

        # Calculate total learning time (sessions with ended_at)
        completed_sessions = LearningSession.objects.filter(
            enrollment__student=user,
            ended_at__isnull=False
        )

        total_learning_time = sum(
            [(session.ended_at - session.started_at).total_seconds()
             for session in completed_sessions],
            0
        ) / 3600  # Convert to hours

        # Get modules completed count
        total_modules_completed = ModuleProgress.objects.filter(
            enrollment__student=user,
            is_completed=True
        ).count()

        # Get content completed count
        total_contents_completed = ContentProgress.objects.filter(
            enrollment__student=user,
            is_completed=True
        ).count()

        context = {
            'enrollments': enrollments[:6],  # Show recent 6
            'total_courses': total_courses,
            'active_courses': active_enrollments.count(),
            'completed_courses': completed_courses,
            'avg_progress': round(avg_progress, 2),
            'recent_sessions': recent_sessions,
            'in_progress': in_progress,
            'total_learning_time': round(total_learning_time, 2),
            'total_modules_completed': total_modules_completed,
            'total_contents_completed': total_contents_completed,
        }

        return self.render_to_response(context)


class InstructorCourseAnalyticsView(LoginRequiredMixin, DetailView):
    """Analytics view for instructors to track student progress in their courses"""
    model = Course
    template_name = 'courses/instructor/course_analytics.html'
    context_object_name = 'course'

    def get_queryset(self):
        # Only show courses owned by the instructor
        return Course.objects.filter(owner=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        course = self.object

        # Get all enrollments for this course
        enrollments = CourseEnrollment.objects.filter(
            course=course
        ).select_related('student').order_by('-enrolled_on')

        # Calculate course statistics
        total_students = enrollments.count()
        active_students = enrollments.filter(status='enrolled').count()
        completed_students = enrollments.filter(status='completed').count()
        avg_progress = enrollments.aggregate(avg=Avg('progress_percentage'))['avg'] or 0

        # Module completion rates
        modules_data = []
        for module in course.modules.all():
            total_contents = module.contents.count()
            module_enrollments = ModuleProgress.objects.filter(
                module=module,
                enrollment__course=course
            )
            completed_count = module_enrollments.filter(is_completed=True).count()
            completion_rate = (completed_count / total_students * 100) if total_students > 0 else 0

            modules_data.append({
                'module': module,
                'total_contents': total_contents,
                'completed_count': completed_count,
                'completion_rate': round(completion_rate, 2)
            })

        # Recent enrollments
        recent_enrollments = enrollments[:10]

        # Get learning sessions for this course
        total_sessions = LearningSession.objects.filter(
            enrollment__course=course
        ).count()

        context.update({
            'enrollments': enrollments,
            'total_students': total_students,
            'active_students': active_students,
            'completed_students': completed_students,
            'avg_progress': round(avg_progress, 2),
            'modules_data': modules_data,
            'recent_enrollments': recent_enrollments,
            'total_sessions': total_sessions,
        })

        return context


class StudentProgressDetailView(LoginRequiredMixin, TemplateResponseMixin, View):
    """Detailed view of a specific student's progress in a course (for instructors)"""
    template_name = 'courses/instructor/student_progress.html'

    def get(self, request, pk, student_id):
        course = get_object_or_404(Course, pk=pk, owner=request.user)
        enrollment = get_object_or_404(
            CourseEnrollment,
            course=course,
            student_id=student_id
        )

        # Get module progress
        modules_progress = []
        for module in course.modules.all():
            module_progress = ModuleProgress.objects.filter(
                enrollment=enrollment,
                module=module
            ).first()

            contents_progress = []
            for content in module.contents.all():
                content_progress = ContentProgress.objects.filter(
                    enrollment=enrollment,
                    content=content
                ).first()
                contents_progress.append({
                    'content': content,
                    'progress': content_progress
                })

            modules_progress.append({
                'module': module,
                'progress': module_progress,
                'contents_progress': contents_progress
            })

        # Get learning sessions
        learning_sessions = LearningSession.objects.filter(
            enrollment=enrollment
        ).select_related('content').order_by('-started_at')[:20]

        context = {
            'course': course,
            'enrollment': enrollment,
            'student': enrollment.student,
            'modules_progress': modules_progress,
            'learning_sessions': learning_sessions,
        }

        return self.render_to_response(context)


class InstructorStudentsOverviewView(LoginRequiredMixin, TemplateResponseMixin, View):
    """Overview of all students across all instructor's courses"""
    template_name = 'courses/instructor/students_overview.html'

    def get(self, request):
        # Get all courses owned by the instructor
        instructor_courses = Course.objects.filter(owner=request.user).prefetch_related('modules')

        # Get all enrollments for instructor's courses
        all_enrollments = CourseEnrollment.objects.filter(
            course__in=instructor_courses
        ).select_related('student', 'course').order_by('-last_accessed')

        # Calculate overall statistics
        total_students = all_enrollments.values('student').distinct().count()
        total_courses = instructor_courses.count()
        total_enrollments = all_enrollments.count()

        # Status breakdown
        active_enrollments = all_enrollments.filter(status='enrolled').count()
        completed_enrollments = all_enrollments.filter(status='completed').count()
        paused_enrollments = all_enrollments.filter(status='paused').count()

        # Average progress
        avg_progress = all_enrollments.aggregate(avg=Avg('progress_percentage'))['avg'] or 0

        # Get unique students with their enrollment data
        students_data = []
        processed_students = set()

        for enrollment in all_enrollments:
            if enrollment.student.id not in processed_students:
                student = enrollment.student
                student_enrollments = all_enrollments.filter(student=student)

                # Calculate student statistics
                student_total_courses = student_enrollments.count()
                student_active_courses = student_enrollments.filter(status='enrolled').count()
                student_completed_courses = student_enrollments.filter(status='completed').count()
                student_avg_progress = student_enrollments.aggregate(
                    avg=Avg('progress_percentage')
                )['avg'] or 0

                # Get latest activity
                latest_enrollment = student_enrollments.order_by('-last_accessed').first()

                students_data.append({
                    'student': student,
                    'total_courses': student_total_courses,
                    'active_courses': student_active_courses,
                    'completed_courses': student_completed_courses,
                    'avg_progress': round(student_avg_progress, 1),
                    'latest_course': latest_enrollment.course if latest_enrollment else None,
                    'last_accessed': latest_enrollment.last_accessed if latest_enrollment else None,
                    'enrollments': list(student_enrollments)
                })

                processed_students.add(student.id)

        # Sort by last accessed (most recent first)
        students_data.sort(key=lambda x: x['last_accessed'] or timezone.datetime.min.replace(tzinfo=timezone.utc),
                           reverse=True)

        # Pagination with multiples of 5
        per_page = request.GET.get('per_page', '5')
        try:
            per_page = int(per_page)
            # Ensure per_page is a multiple of 5 between 5 and 50
            if per_page not in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:
                per_page = 5
        except (ValueError, TypeError):
            per_page = 5

        paginator = Paginator(students_data, per_page)
        page_number = request.GET.get('page', 1)
        students_page = paginator.get_page(page_number)

        # Available per_page options (multiples of 5)
        per_page_options = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

        # Course-wise enrollment statistics
        courses_data = []
        for course in instructor_courses:
            course_enrollments = all_enrollments.filter(course=course)
            course_total_students = course_enrollments.count()
            course_active_students = course_enrollments.filter(status='enrolled').count()
            course_completed_students = course_enrollments.filter(status='completed').count()
            course_avg_progress = course_enrollments.aggregate(
                avg=Avg('progress_percentage')
            )['avg'] or 0

            courses_data.append({
                'course': course,
                'total_students': course_total_students,
                'active_students': course_active_students,
                'completed_students': course_completed_students,
                'avg_progress': round(course_avg_progress, 1)
            })

        context = {
            'total_students': total_students,
            'total_courses': total_courses,
            'total_enrollments': total_enrollments,
            'active_enrollments': active_enrollments,
            'completed_enrollments': completed_enrollments,
            'paused_enrollments': paused_enrollments,
            'avg_progress': round(avg_progress, 1),
            'students_data': students_page,  # Use paginated data
            'courses_data': courses_data,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }

        return self.render_to_response(context)


class InstructorCourseStudentsView(LoginRequiredMixin, TemplateResponseMixin, View):
    """Detailed view of all students in a specific course"""
    template_name = 'courses/instructor/course_students.html'

    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk, owner=request.user)

        # Get all enrollments for this course
        enrollments = CourseEnrollment.objects.filter(
            course=course
        ).select_related('student').order_by('-last_accessed')

        # Calculate statistics
        total_students = enrollments.count()
        active_students = enrollments.filter(status='enrolled').count()
        completed_students = enrollments.filter(status='completed').count()
        paused_students = enrollments.filter(status='paused').count()
        avg_progress = enrollments.aggregate(avg=Avg('progress_percentage'))['avg'] or 0

        # Get module completion data for each student
        students_detailed = []
        for enrollment in enrollments:
            # Get module progress
            modules_progress = ModuleProgress.objects.filter(
                enrollment=enrollment
            ).select_related('module')

            completed_modules = modules_progress.filter(is_completed=True).count()
            total_modules = course.modules.count()

            # Get content progress
            content_progress = ContentProgress.objects.filter(
                enrollment=enrollment
            )

            completed_contents = content_progress.filter(is_completed=True).count()
            total_contents = Content.objects.filter(module__course=course).count()

            # Get recent learning sessions
            recent_sessions = LearningSession.objects.filter(
                enrollment=enrollment
            ).order_by('-started_at')[:5]

            students_detailed.append({
                'enrollment': enrollment,
                'student': enrollment.student,
                'completed_modules': completed_modules,
                'total_modules': total_modules,
                'completed_contents': completed_contents,
                'total_contents': total_contents,
                'recent_sessions': recent_sessions,
            })

        # Module-wise completion statistics
        modules_stats = []
        for module in course.modules.all():
            module_progress_all = ModuleProgress.objects.filter(
                module=module,
                enrollment__course=course
            )
            completed_count = module_progress_all.filter(is_completed=True).count()
            completion_rate = (completed_count / total_students * 100) if total_students > 0 else 0

            modules_stats.append({
                'module': module,
                'completed_count': completed_count,
                'completion_rate': round(completion_rate, 1)
            })

        # Pagination with multiples of 5
        per_page = request.GET.get('per_page', '5')
        try:
            per_page = int(per_page)
            # Ensure per_page is a multiple of 5 between 5 and 50
            if per_page not in [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]:
                per_page = 5
        except (ValueError, TypeError):
            per_page = 5

        paginator = Paginator(students_detailed, per_page)
        page_number = request.GET.get('page', 1)
        students_page = paginator.get_page(page_number)

        # Available per_page options (multiples of 5)
        per_page_options = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50]

        context = {
            'course': course,
            'enrollments': enrollments,
            'students_detailed': students_page,
            'total_students': total_students,
            'active_students': active_students,
            'completed_students': completed_students,
            'paused_students': paused_students,
            'avg_progress': round(avg_progress, 1),
            'modules_stats': modules_stats,
            'per_page': per_page,
            'per_page_options': per_page_options,
        }

        return self.render_to_response(context)


class CourseWaitlistManagementView(LoginRequiredMixin, TemplateResponseMixin, View):
    """Manage course waitlist and approve enrollments from waitlist"""
    template_name = 'courses/instructor/waitlist_management.html'

    def get(self, request, pk):
        course = get_object_or_404(Course, pk=pk, owner=request.user)

        # Get waitlist entries
        waitlist_entries = CourseWaitlist.objects.filter(
            course=course
        ).select_related('student').order_by('priority', 'joined_waitlist')

        # Get pending enrollments
        pending_enrollments = CourseEnrollment.objects.filter(
            course=course,
            status='pending'
        ).select_related('student').order_by('enrolled_on')

        # Get recent rejected enrollments
        rejected_enrollments = CourseEnrollment.objects.filter(
            course=course,
            status='rejected'
        ).select_related('student', 'approved_by').order_by('-approved_at')[:10]

        # Calculate capacity statistics
        current_enrolled = course.get_enrollment_count()
        capacity_remaining = (course.max_capacity - current_enrolled) if course.max_capacity else None

        context = {
            'course': course,
            'waitlist_entries': waitlist_entries,
            'pending_enrollments': pending_enrollments,
            'rejected_enrollments': rejected_enrollments,
            'current_enrolled': current_enrolled,
            'capacity_remaining': capacity_remaining,
            'has_capacity': course.max_capacity is None or capacity_remaining > 0,
            'waitlist_count': waitlist_entries.count(),
            'pending_count': pending_enrollments.count(),
        }

        return self.render_to_response(context)


class ApproveWaitlistEntryView(LoginRequiredMixin, View):
    """Approve a waitlist entry and create enrollment"""

    def post(self, request, pk):
        waitlist_entry = get_object_or_404(CourseWaitlist, pk=pk)
        course = waitlist_entry.course
        student = waitlist_entry.student

        # Check permissions
        if not (request.user == course.owner or request.user.is_staff):
            messages.error(request, 'You do not have permission to approve waitlist entries.')
            return redirect('course_waitlist_management', pk=course.pk)

        # Check if course has capacity
        if course.is_full():
            messages.error(request, 'Cannot approve: course is at capacity.')
            return redirect('course_waitlist_management', pk=course.pk)

        # Check if student is already enrolled
        if CourseEnrollment.objects.filter(student=student, course=course, status__in=['enrolled', 'pending']).exists():
            messages.error(request, 'Student is already enrolled or has pending enrollment.')
            waitlist_entry.delete()
            return redirect('course_waitlist_management', pk=course.pk)

        # Create enrollment
        enrollment = CourseEnrollment.objects.create(
            student=student,
            course=course,
            status='enrolled' if course.enrollment_type == 'open' else 'pending',
            approved_by=request.user,
            approved_at=timezone.now()
        )

        if course.enrollment_type == 'open':
            # Direct enrollment for open courses
            course.students.add(student)

            # Create initial module progress
            first_module = course.modules.order_by('order').first()
            if first_module:
                ModuleProgress.objects.create(
                    enrollment=enrollment,
                    module=first_module
                )

            messages.success(request, f'Approved and enrolled {student.get_full_name()} from waitlist.')
        else:
            # Requires additional approval for restricted courses
            messages.success(request, f'Moved {student.get_full_name()} from waitlist to pending approval.')

        # Remove from waitlist
        waitlist_entry.delete()

        return redirect('course_waitlist_management', pk=course.pk)


class CourseQuickStatusView(LoginRequiredMixin, View):
    """Quick status change for courses from the management dashboard"""

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk, owner=request.user)
        new_status = request.POST.get('status')

        # Validate status
        valid_statuses = ['draft', 'published', 'archived']
        if new_status not in valid_statuses:
            messages.error(request, 'Status tidak valid.')
            return redirect('manage_course_list')

        old_status = course.status
        course.status = new_status
        course.save()

        # Status change messages
        status_messages = {
            'published': f'Kursus "{course.title}" berhasil dipublikasikan dan sekarang terlihat oleh siswa.',
            'draft': f'Kursus "{course.title}" diubah ke draft. Siswa baru tidak dapat melihat kursus ini.',
            'archived': f'Kursus "{course.title}" diarsipkan. Kursus tidak lagi terlihat di publik.'
        }

        messages.success(request, status_messages.get(new_status, f'Status kursus diubah ke {new_status}.'))

        # Return JSON response for HTMX or redirect for regular forms
        if request.headers.get('HX-Request'):
            return JsonResponse({
                'status': 'success',
                'message': status_messages.get(new_status),
                'new_status': new_status,
                'old_status': old_status
            })

        return redirect('manage_course_list')


class BulkContentOperationsView(LoginRequiredMixin, View):
    """Bulk operations for content management"""

    def post(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        operation = request.POST.get('operation')
        content_ids = request.POST.getlist('content_ids')

        if not content_ids:
            messages.error(request, 'Tidak ada konten yang dipilih.')
            return redirect('module_content_list', module_id=module.id)

        if operation == 'delete':
            # Bulk delete selected content
            deleted_count = 0
            for content_id in content_ids:
                try:
                    content = get_object_or_404(Content, id=content_id, module=module)
                    # Delete all content items and their actual items
                    for content_item in content.items.all():
                        if content_item.item:
                            content_item.item.delete()
                    content.delete()
                    deleted_count += 1
                except Exception as e:
                    messages.error(request, f'Error deleting content ID {content_id}: {str(e)}')

            if deleted_count > 0:
                messages.success(request, f'{deleted_count} konten berhasil dihapus.')

        elif operation == 'duplicate':
            # Bulk duplicate selected content
            duplicated_count = 0
            for content_id in content_ids:
                try:
                    original_content = get_object_or_404(Content, id=content_id, module=module)

                    # Create duplicate content
                    new_content = Content.objects.create(
                        module=module,
                        title=f"{original_content.title} (Copy)",
                        order=original_content.order + 100  # Place at end
                    )

                    # Duplicate all content items
                    for content_item in original_content.items.all():
                        if content_item.item:
                            original_item = content_item.item

                            # Create copy of the content item
                            new_item = type(original_item).objects.create(
                                owner=request.user,
                                title=f"{original_item.title} (Copy)",
                                created=timezone.now(),
                                updated=timezone.now()
                            )

                            # Copy type-specific fields
                            if hasattr(original_item, 'text'):
                                new_item.text = original_item.text
                            elif hasattr(original_item, 'file'):
                                new_item.file = original_item.file
                            elif hasattr(original_item, 'url'):
                                new_item.url = original_item.url
                                if hasattr(original_item, 'video_platform'):
                                    new_item.video_platform = original_item.video_platform
                                if hasattr(original_item, 'duration'):
                                    new_item.duration = original_item.duration
                                if hasattr(original_item, 'transcript'):
                                    new_item.transcript = original_item.transcript
                                if hasattr(original_item, 'captions_enabled'):
                                    new_item.captions_enabled = original_item.captions_enabled
                                if hasattr(original_item, 'auto_play'):
                                    new_item.auto_play = original_item.auto_play
                                if hasattr(original_item, 'minimum_watch_percentage'):
                                    new_item.minimum_watch_percentage = original_item.minimum_watch_percentage

                            new_item.save()

                            # Create content item relationship
                            ContentItem.objects.create(
                                content=new_content,
                                item=new_item,
                                order=content_item.order
                            )

                    duplicated_count += 1
                except Exception as e:
                    messages.error(request, f'Error duplicating content ID {content_id}: {str(e)}')

            if duplicated_count > 0:
                messages.success(request, f'{duplicated_count} konten berhasil diduplikasi.')

        elif operation == 'reorder':
            # Bulk reorder - expect order data in request
            order_data = request.POST.get('order_data')  # JSON string of {id: order, ...}
            if order_data:
                try:
                    import json
                    orders = json.loads(order_data)
                    for content_id, order in orders.items():
                        Content.objects.filter(
                            id=int(content_id),
                            module=module
                        ).update(order=int(order))
                    messages.success(request, 'Urutan konten berhasil diperbarui.')
                except Exception as e:
                    messages.error(request, f'Error reordering content: {str(e)}')

        elif operation == 'change_module':
            # Move content to another module
            target_module_id = request.POST.get('target_module_id')
            if target_module_id:
                try:
                    target_module = get_object_or_404(
                        Module,
                        id=target_module_id,
                        course__owner=request.user
                    )
                    moved_count = 0
                    for content_id in content_ids:
                        content = get_object_or_404(Content, id=content_id, module=module)
                        content.module = target_module
                        content.save()
                        moved_count += 1

                    if moved_count > 0:
                        messages.success(
                            request,
                            f'{moved_count} konten berhasil dipindah ke modul "{target_module.title}".'
                        )
                except Exception as e:
                    messages.error(request, f'Error moving content: {str(e)}')

        else:
            messages.error(request, 'Operasi tidak valid.')

        return redirect('module_content_list', module_id=module.id)


class BulkContentItemOperationsView(LoginRequiredMixin, View):
    """Bulk operations for content items within a content"""

    def post(self, request, content_id):
        content = get_object_or_404(Content, id=content_id, module__course__owner=request.user)
        operation = request.POST.get('operation')
        item_ids = request.POST.getlist('item_ids')

        if not item_ids:
            messages.error(request, 'Tidak ada item yang dipilih.')
            return redirect('module_content_list', module_id=content.module.id)

        if operation == 'delete':
            # Bulk delete selected content items
            deleted_count = 0
            for item_id in item_ids:
                try:
                    content_item = get_object_or_404(
                        ContentItem,
                        id=item_id,
                        content=content
                    )
                    if content_item.item:
                        content_item.item.delete()
                    content_item.delete()
                    deleted_count += 1
                except Exception as e:
                    messages.error(request, f'Error deleting item ID {item_id}: {str(e)}')

            if deleted_count > 0:
                messages.success(request, f'{deleted_count} item konten berhasil dihapus.')

        elif operation == 'reorder':
            # Bulk reorder content items
            order_data = request.POST.get('order_data')  # JSON string
            if order_data:
                try:
                    import json
                    orders = json.loads(order_data)
                    for item_id, order in orders.items():
                        ContentItem.objects.filter(
                            id=int(item_id),
                            content=content
                        ).update(order=int(order))
                    messages.success(request, 'Urutan item konten berhasil diperbarui.')
                except Exception as e:
                    messages.error(request, f'Error reordering items: {str(e)}')

        else:
            messages.error(request, 'Operasi tidak valid.')

        return redirect('module_content_list', module_id=content.module.id)


class RemoveWaitlistEntryView(LoginRequiredMixin, View):
    """Remove a student from waitlist"""

    def post(self, request, pk):
        waitlist_entry = get_object_or_404(CourseWaitlist, pk=pk)
        course = waitlist_entry.course
        student = waitlist_entry.student

        # Check permissions
        if not (request.user == course.owner or request.user.is_staff):
            messages.error(request, 'You do not have permission to manage waitlist.')
            return redirect('course_waitlist_management', pk=course.pk)

        # Get removal reason
        removal_reason = request.POST.get('removal_reason', 'No reason provided')

        # Remove from waitlist
        waitlist_entry.delete()

        messages.success(request, f'Removed {student.get_full_name()} from waitlist.')

        return redirect('course_waitlist_management', pk=course.pk)
