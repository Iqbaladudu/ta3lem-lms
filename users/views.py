from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LogoutView
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView
from django.views.generic.edit import CreateView, FormView
from django.shortcuts import redirect, get_object_or_404, render
from courses.models import Course
from .forms import CourseEnrollForm, StudentRegistrationForm, StudentLoginForm, InstructorLoginForm, ResendEmailVerificationForm
from .models import User
from django.views import View

class StudentOnlyRedirectMixin:
    def dispatch(self, request, *args, **kwargs):
        is_authenticated = request.user.is_authenticated

        if not is_authenticated:
            return redirect('student_login')

        return super().dispatch(request, *args, **kwargs)

class UserAlreadyAuthenticatedMixin:
    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            print(request.user.is_authenticated)
            if request.user.is_student():
                return redirect('student_course_list')
            elif request.user.is_instructor():
                return redirect('manage_course_list')
        return super().dispatch(request, *args, **kwargs)

class StudentCourseDetailView(LoginRequiredMixin, StudentOnlyRedirectMixin, DetailView):
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


class StudentCourseListView(LoginRequiredMixin, StudentOnlyRedirectMixin, ListView):
    model = Course
    template_name = "users/course/list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(students__in=[self.request.user])


class StudentEnrollCourseView(LoginRequiredMixin, StudentOnlyRedirectMixin, FormView):
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
    # success_url = reverse_lazy("student_course_list")

    def form_valid(self, form):
        # Save the form first to create the user object
        user = form.save(commit=False)
        user.role = 'student'
        user.is_active = False
        user.save()

        # generate token dan link
        token = default_token_generator.make_token(user)
        uid = user.pk
        link = self.request.build_absolute_uri(reverse('verify_email', kwargs={'id': uid, 'token': token}))

        subject = 'Verify your email address'
        message = f'Hi {user.username}, please click the link to verify your email address: {link}'
        user.email_user(subject, message)

        if self.request.htmx:
            return render(self.request, 'users/student/registration_success.html')

        return redirect('student_login')

    def form_invalid(self, form):
        if self.request.htmx:
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_invalid(form)


class StudentLoginView(UserAlreadyAuthenticatedMixin, FormView):
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


class InstructorLoginView(UserAlreadyAuthenticatedMixin ,FormView):
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

def verify_email(request, id, token):
    user = get_object_or_404(User, pk=id)
    if default_token_generator.check_token(user, token):
        user.is_active = True
        user.save()
        login(request, user)
        return render(request, 'users/student/email_verification_success.html')
    else:
        return render(request, 'users/student/email_verification_failed.html')

class ResendEmailVerificationView(FormView):
    template_name = "users/student/resend_verification_email.html"
    form_class = ResendEmailVerificationForm
    success_url = reverse_lazy('student_login')

    def form_valid(self, form):
        email = form.cleaned_data['email']
        user = get_object_or_404(User, email=email, role='student', is_active=False)

        # generate token dan link
        token = default_token_generator.make_token(user)
        uid = user.pk
        link = self.request.build_absolute_uri(reverse('verify_email', kwargs={'id': uid, 'token': token}))

        subject = 'Verify your email address'
        message = f'Hi {user.username}, please click the link to verify your email address: {link}'
        user.email_user(subject, message)

        if self.request.htmx:
            return render(self.request, 'users/student/resend_verification_email_success.html')

        return super().form_valid(form)

    def form_invalid(self, form):
        if self.request.htmx:
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_invalid(form)
