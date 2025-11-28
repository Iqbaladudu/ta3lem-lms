from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.db.models import Q, Avg
from django.db.models.aggregates import Count
from django.forms import modelform_factory
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

from users.forms import CourseEnrollForm
from .forms import ModuleFormSets
from .models import (
    Course, Module, Content, Subject, CourseEnrollment,
    ContentProgress, ModuleProgress, LearningSession
)

class CourseListView(ListView):
    model = Course
    template_name = 'courses/course/list.html'
    paginate_by = 4  # Show 6 courses per page
    context_object_name = 'courses'

    def get_queryset(self):
        subject_slug = self.kwargs.get('subject')
        cache_key = f"course_list_queryset_{subject_slug}" if subject_slug else "course_list_queryset"
        queryset = cache.get(cache_key)
        if queryset is None:
            queryset = Course.objects.annotate(total_modules=Count('modules')).order_by('-created')
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
            subjects = Subject.objects.annotate(total_courses=Count('courses'))
            cache.set('all_subjects', subjects)
        context['subjects'] = subjects

        # Get current subject if filtering
        subject_slug = self.kwargs.get('subject')
        if subject_slug:
            context['subject'] = get_object_or_404(Subject, slug=subject_slug)
        else:
            context['subject'] = None

        return context


@method_decorator(cache_page(60 * 15), name='dispatch')
class CourseDetailView(DetailView):
    model = Course
    template_name = 'courses/course/detail.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['enroll_form'] = CourseEnrollForm(
            initial={'course': self.object}
        )
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


class ContentCreateUpdateView(TemplateResponseMixin, View):
    module = None
    model = None
    obj = None
    template_name = 'courses/manage/content/form.html'

    @staticmethod
    def get_model(model_name):
        if model_name in ['text', 'video', 'image', 'file']:
            return apps.get_model(app_label='courses', model_name=model_name)
        return None

    @staticmethod
    def get_form(model, *args, **kwargs):
        Form = modelform_factory(model, exclude=['owner', 'order', 'created', 'updated'])
        return Form(*args, **kwargs)

    def dispatch(self, request, module_id, model_name, id=None):
        self.module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        self.model = self.get_model(model_name)
        if id:
            self.obj = get_object_or_404(self.model, id=id, owner=request.user)
        return super().dispatch(request, module_id, model_name, id)

    def get(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj)
        return self.render_to_response({'form': form, 'object': self.obj})

    def post(self, request, module_id, model_name, id=None):
        form = self.get_form(self.model, instance=self.obj, data=request.POST, files=request.FILES)
        if form.is_valid():
            obj = form.save(commit=False)
            obj.owner = request.user
            obj.save()
            if not id:
                Content.objects.create(module=self.module, item=obj)
            return redirect('module_content_list', self.module.id)
        return self.render_to_response({'form': form, 'object': self.obj})


class ModuleContentListView(TemplateResponseMixin, View):
    template_name = 'courses/manage/module/content_list.html'

    def get(self, request, module_id):
        module = get_object_or_404(Module, id=module_id, course__owner=request.user)
        return self.render_to_response({'module': module})


class ContentDeleteView(View):
    def post(self, request, id):
        content = get_object_or_404(Content, id=id, module__course__owner=request.user)
        module = content.module
        content.item.delete()
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
    fields = ["subject", "title", "slug", "overview"]
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


class CourseUpdateView(OwnerCourseEditMixin, UpdateView):
    permission_required = 'courses.change_course'


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
    """Handle student course enrollment"""

    def post(self, request, pk):
        course = get_object_or_404(Course, pk=pk)

        # Check if already enrolled
        enrollment, created = CourseEnrollment.objects.get_or_create(
            student=request.user,
            course=course,
            defaults={'status': 'enrolled'}
        )

        if created:
            # Add student to course's students M2M field
            course.students.add(request.user)

            # Create initial module progress for first module
            first_module = course.modules.order_by('order').first()
            if first_module:
                ModuleProgress.objects.create(
                    enrollment=enrollment,
                    module=first_module
                )

        return redirect('student_course_detail', pk=course.pk)


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

        # Add statistics
        all_enrollments = CourseEnrollment.objects.filter(student=self.request.user)
        context['total_courses'] = all_enrollments.count()
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
        next_content = all_contents[current_index + 1] if current_index is not None and current_index < len(all_contents) - 1 else None

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


