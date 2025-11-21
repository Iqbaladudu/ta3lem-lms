from django.conf import settings
from django.urls import path, include
from django.views.decorators.cache import cache_page

from . import views


urlpatterns = [
    # Authentication URLs
    path('logout', views.UserLogoutView.as_view(), name="logout"),
    path('login/', views.StudentLoginView.as_view(), name='student_login'),
    path('register/', views.StudentRegistrationView.as_view(), name='student_registration'),
    path('instructor/', views.InstructorLoginView.as_view(), name='instructor_login'),

    # Student Course URLs
    path("enroll/", views.StudentEnrollCourseView.as_view(), name="student_enroll_course"),
    path(
        'courses/',
        views.StudentCourseListView.as_view(),
        name='student_course_list'
    ),
    path(
        'courses/<pk>/',
        cache_page(60 * 15)(views.StudentCourseDetailView.as_view()),
        name='student_course_detail'
    ),
    path(
        'courses/<pk>/<module_id>/', views.StudentCourseDetailView.as_view(),
        name='student_course_detail_module'
    ),
    path('verify-email/<int:id>/<str:token>/', views.verify_email, name='verify_email'),
    path('resend-verification/', views.ResendEmailVerificationView.as_view(), name='resend_email_verification'),
]
