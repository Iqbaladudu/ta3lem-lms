from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, FormView
from django.shortcuts import redirect
from courses.models import Course
from .forms import CourseEnrollForm, StudentRegistrationForm, StudentLoginForm, InstructorLoginForm


class StudentCourseDetailView(LoginRequiredMixin, DetailView):
    model = Course
    template_name = "users/course/detail.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get course object
        course = self.get_object()
        if 'module_id' in self.kwargs:
            # get current module
            context['module'] = course.modules.get(id=self.kwargs['module_id'])
        else:
            context['module'] = course.modules.all()[0]
        return context


class StudentCourseListView(LoginRequiredMixin, ListView):
    model = Course
    template_name = "users/course/list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])


class StudentEnrollCourseView(LoginRequiredMixin, FormView):
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        self.course = form.cleaned_data['course']
        self.course.students.add(self.request.user)
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('student_course_detail', args=[self.course.id])


class StudentRegistrationView(CreateView):
    template_name = "users/student/registration.html"
    form_class = StudentRegistrationForm
    success_url = reverse_lazy("student_course_list")

    def form_valid(self, form):
        result = super().form_valid(form)
        cd = form.cleaned_data
        user = self.object
        user.role = 'student'
        user.is_active = True
        user.save()
        user = authenticate(username=cd['username'], password=cd['password1'])
        login(self.request, user)
        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response
        return result

    def form_invalid(self, form):
        if self.request.htmx:
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_invalid(form)


class StudentLoginView(FormView):
    template_name = "users/student/login.html"
    form_class = StudentLoginForm
    success_url = reverse_lazy("student_course_list")

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '')
        return context


class InstructorLoginView(FormView):
    template_name = "users/instructor/login.html"
    form_class = InstructorLoginForm
    success_url = reverse_lazy("manage_course_list")

    def form_valid(self, form):
        user = form.get_user()
        # Verify that the user is an instructor
        if user.role != 'instructor':
            form.add_error(None, "You must be an instructor to log in here.")
            return self.form_invalid(form)

        login(self.request, user)
        if self.request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(self.success_url)
            return response
        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.htmx:
            # Return only the form part for HTMX requests to prevent duplication
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['next'] = self.request.GET.get('next', '')
        return context

class UserLogoutView(LogoutView):
    # template_name = "users/logout.html"

    def post(self, request, *args, **kwargs):
        user = request.user
        is_student = user.is_student()
        is_instructor = user.is_instructor()

        # Logout the user
        logout(request)

        # Determine redirect URL based on role
        if is_student:
            redirect_url = reverse_lazy("student_login")
        elif is_instructor:
            redirect_url = reverse_lazy("instructor_login")
        else:
            redirect_url = reverse_lazy("student_login")

        # Handle HTMX requests
        if request.htmx:
            response = HttpResponse()
            response['HX-Redirect'] = str(redirect_url)
            return response

        # Handle regular requests
        return redirect(redirect_url)

