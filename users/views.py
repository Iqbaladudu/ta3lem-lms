from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.views import LogoutView
from django.http import HttpResponse
from django.urls import reverse_lazy, reverse
from django.views.generic import ListView, DetailView, TemplateView
from django.views.generic.edit import CreateView, FormView
from django.shortcuts import redirect, get_object_or_404, render
from courses.models import Course
from .forms import CourseEnrollForm, StudentRegistrationForm, StudentLoginForm, InstructorLoginForm, ResendEmailVerificationForm
from .models import User
from django.core.cache import cache

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
        return qs.filter(course_enrollments__student=self.request.user)
    
    def dispatch(self, request, *args, **kwargs):
        """Check if user has valid access to the course"""
        from courses.access_service import CourseAccessService
        
        # Get the course first
        self.object = self.get_object()
        
        # Check access
        can_access, reason = CourseAccessService.can_access_course(request.user, self.object)
        
        if not can_access:
            if reason == 'subscription_expired':
                messages.warning(request, 'Langganan Anda telah berakhir. Silakan perpanjang untuk melanjutkan akses.')
                return redirect('subscriptions:plans')
            elif reason == 'not_enrolled':
                messages.warning(request, 'Anda belum terdaftar di kursus ini.')
                return redirect('course_detail', pk=self.object.id)
            else:
                messages.error(request, 'Anda tidak memiliki akses ke kursus ini.')
                return redirect('student_course_list')
        
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # get course object
        course = self.get_object()
        if 'module_id' in self.kwargs:
            # get current module
            context['module'] = course.modules.get(id=self.kwargs['module_id'])
        else:
            context['module'] = course.modules.all()[0]
        
        # Add enrollment object to context
        context['enrollment'] = course.course_enrollments.filter(student=self.request.user).first()
        return context


class StudentCourseListView(LoginRequiredMixin, StudentOnlyRedirectMixin, ListView):
    model = Course
    template_name = "users/course/list.html"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(course_enrollments__student=self.request.user)


class StudentEnrollCourseView(LoginRequiredMixin, StudentOnlyRedirectMixin, FormView):
    course = None
    form_class = CourseEnrollForm

    def form_valid(self, form):
        from courses.access_service import EnrollmentService
        from subscriptions.services import SubscriptionService
        from django.contrib import messages
        
        self.course = form.cleaned_data['course']
        
        # Check pricing type and handle accordingly
        if self.course.pricing_type == 'free':
            # Free course - enroll directly
            EnrollmentService.enroll_free(self.request.user, self.course)
            messages.success(self.request, f'Berhasil mendaftar ke kursus {self.course.title}')
            
        elif self.course.pricing_type == 'subscription_only':
            # Subscription only - must have active subscription
            subscription = SubscriptionService.get_active_subscription(self.request.user)
            if subscription:
                EnrollmentService.enroll_with_subscription(
                    self.request.user, 
                    self.course, 
                    subscription
                )
                messages.success(self.request, f'Berhasil mendaftar ke kursus {self.course.title}')
            else:
                # No active subscription - redirect to subscription page
                messages.warning(self.request, 'Kursus ini hanya tersedia untuk pelanggan. Silakan pilih paket langganan.')
                return redirect('subscriptions:plans')
                
        elif self.course.pricing_type == 'one_time':
            # One-time purchase - redirect to payment
            messages.info(self.request, 'Silakan lakukan pembayaran untuk mengakses kursus ini.')
            return redirect('course_detail', pk=self.course.id)
            
        elif self.course.pricing_type == 'both':
            # Both options - need to choose
            messages.info(self.request, 'Silakan pilih metode pembayaran: beli sekali atau berlangganan.')
            return redirect('course_detail', pk=self.course.id)
        
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
            return render(self.request, 'users/student/registration_success_partial.html')

        return redirect('student_login')

    def form_invalid(self, form):
        if self.request.htmx:
            # HTMX will select only #registration-form-wrapper content using hx-select
            return self.render_to_response(self.get_context_data(form=form))
        return super().form_invalid(form)


class StudentLoginView(UserAlreadyAuthenticatedMixin, FormView):
    template_name = "users/student/login.html"
    form_class = StudentLoginForm
    success_url = reverse_lazy("student_course_list")

    # recreate cache in main view after login
    course_list_url = reverse_lazy("course_list")
    coursee_list_cache_key = f'course'

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


class StudentDashboardView(LoginRequiredMixin, StudentOnlyRedirectMixin, TemplateView):
    """Dashboard view with subscription info for students"""
    template_name = 'users/student/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get enrolled courses
        enrolled_courses = Course.objects.filter(
            course_enrollments__student=self.request.user
        )[:3]  # Show latest 3
        
        context['enrolled_courses'] = enrolled_courses
        context['total_courses'] = enrolled_courses.count()
        
        return context

