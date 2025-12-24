from django.urls import path, include

from . import views

urlpatterns = [
    # Instructor/Owner Course Management
    path("mine/", views.ManageCourseListView.as_view(), name="manage_course_list"),
    path("create/", views.CourseCreateView.as_view(), name="course_create"),
    path("<int:pk>/edit/", views.CourseUpdateView.as_view(), name="course_edit"),
    path("<int:pk>/status/", views.CourseQuickStatusView.as_view(), name="course_quick_status"),
    path("<int:pk>/delete/", views.CourseDeleteView.as_view(), name="course_delete"),
    path("<int:pk>/module/", views.CourseModuleUpdateView.as_view(), name="course_module_update"),

    # Module and Content Management
    path("module/<int:module_id>/content/<model_name>/create/", views.ContentCreateUpdateView.as_view(),
         name="module_content_create"),
    path("module/<int:module_id>/content/<model_name>/<int:id>/", views.ContentCreateUpdateView.as_view(),
         name="module_content_update"),
    # Tambah item ke Content yang sudah ada
    path("module/<int:module_id>/content/<model_name>/create/<int:content_id>/", views.ContentCreateUpdateView.as_view(),
         name="module_content_add_item"),
    # ContentItem management
    path("content/<int:content_id>/item/<model_name>/create/", views.ContentItemCreateView.as_view(),
         name="content_item_create"),
    path("content/<int:content_id>/item/<int:item_id>/delete/", views.ContentItemDeleteView.as_view(),
         name="content_item_delete"),
    path("content/<int:content_id>/title/", views.ContentTitleUpdateView.as_view(),
         name="content_title_update"),
    path("content-item/order/", views.ContentItemOrderView.as_view(), name="content_item_order"),
    # Content delete
    path("content/<int:id>/delete/", views.ContentDeleteView.as_view(), name="module_content_delete"),

    path("module/<int:module_id>/", views.ModuleContentListView.as_view(), name="module_content_list"),
    path("module/<int:module_id>/bulk/", views.BulkContentOperationsView.as_view(), name="bulk_content_operations"),
    path("content/<int:content_id>/bulk/", views.BulkContentItemOperationsView.as_view(), name="bulk_content_item_operations"),
    path("module/order/", views.ModuleOrderView.as_view(), name="module_order"),
    path("content/order/", views.ContentOrderView.as_view(), name="content_order"),

    # Student Course Tracking
    path("student/dashboard/", views.StudentDashboardView.as_view(), name="student_dashboard"),
    path("student/courses/", views.StudentCourseListView.as_view(), name="student_course_list"),
    path("student/<int:pk>/enroll/", views.StudentEnrollCourseView.as_view(), name="student_enroll_course"),
    path("student/<int:pk>/waitlist/", views.StudentJoinWaitlistView.as_view(), name="student_join_waitlist"),
    path("student/<int:pk>/", views.StudentCourseDetailView.as_view(), name="student_course_detail"),
    # Module detail page removed - navigation now goes directly from course to content with sidebar
    path("student/<int:pk>/module/<int:module_pk>/", views.StudentModuleDetailView.as_view(), name="student_module_detail"),
    path("student/<int:pk>/module/<int:module_pk>/content/<int:content_pk>/", views.StudentContentView.as_view(), name="student_content_view"),
    path("student/<int:pk>/module/<int:module_pk>/content/<int:content_pk>/complete/", views.MarkContentCompleteView.as_view(), name="mark_content_complete"),

    # Instructor Analytics
    path("analytics/<int:pk>/", views.InstructorCourseAnalyticsView.as_view(), name="instructor_course_analytics"),
    path("analytics/<int:pk>/student/<int:student_id>/", views.StudentProgressDetailView.as_view(), name="instructor_student_progress"),
    
    # Enrollment Management
    path("enrollment/<int:pk>/approve/", views.ApproveEnrollmentView.as_view(), name="approve_enrollment"),
    path("enrollment/<int:pk>/reject/", views.RejectEnrollmentView.as_view(), name="reject_enrollment"),
    path("waitlist/<int:pk>/manage/", views.CourseWaitlistManagementView.as_view(), name="course_waitlist_management"),
    path("waitlist/entry/<int:pk>/approve/", views.ApproveWaitlistEntryView.as_view(), name="approve_waitlist_entry"),
    path("waitlist/entry/<int:pk>/remove/", views.RemoveWaitlistEntryView.as_view(), name="remove_waitlist_entry"),

    # Instructor Student Management
    path("students/overview/", views.InstructorStudentsOverviewView.as_view(), name="instructor_students_overview"),
    path("students/<int:pk>/", views.InstructorCourseStudentsView.as_view(), name="instructor_course_students"),

    # Public Course Listing
    path('subject/<slug:subject>/', views.CourseListView.as_view(), name='course_list_subject'),
    path('<slug:slug>/', views.CourseDetailView.as_view(), name='course_detail'),
    path('__debug__/', include('debug_toolbar.urls')),
]
