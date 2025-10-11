from django.conf import settings
from django.urls import path, include
from django.views.decorators.cache import cache_page

from . import views

urlpatterns = [
    path("register/", views.StudentRegistrationView.as_view(), name="student_registration"),
    path("enroll/", views.StudentEnrollCourseView.as_view(), name="student_enroll_course"),
    path(
        'courses/',
        views.StudentCourseListView.as_view(),
        name='student_course_list'
    ),
    path(
        'course/<pk>/',
        cache_page(60 * 15)(views.StudentCourseDetailView.as_view()),
        name='student_course_detail'
    ),
    path(
        'course/<pk>/<module_id>/',
        cache_page(60 * 15)(views.StudentCourseDetailView.as_view()),
        name='student_course_detail_module'
    ),
]

if settings.DEBUG:
    # Include django_browser_reload URLs only in DEBUG mode
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]
