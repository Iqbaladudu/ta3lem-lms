from traceback import print_tb

from braces.views import CsrfExemptMixin, JsonRequestResponseMixin
from django.apps import apps
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.cache import cache
from django.db.models import Q
from django.db.models.aggregates import Count
from django.forms import modelform_factory
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import DetailView
from django.views.generic.base import TemplateResponseMixin, View
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView

from users.forms import CourseEnrollForm
from .forms import ModuleFormSets
from .models import Course, Module, Content, Subject
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

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
