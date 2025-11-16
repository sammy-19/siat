from django.urls import path
from .views import *
from .views_auth import StudentLoginView

app_name = 'student_portal'

urlpatterns = [
    path('login/', StudentLoginView.as_view(), name='student_login'),
    path('', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
    path('courses/', courses, name='courses'),
    path('assignments/', assignments, name='assignments'),
    path('materials/', materials, name='materials'),
    path("subject/<int:pk>/", subject_detail, name="subject_detail"),
    path('semester/', semester, name='semester'),
    path('course/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('assignment/<int:pk>/', AssignmentDetailView.as_view(), name='assignment_detail'),
    path('download/<int:assignment_id>/', download_pdf, name='download_pdf'),
    path('notifications/', get_notifications, name='get_notifications'),
    path('notifications/<int:notification_id>/read/', mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', mark_all_notifications_read, name='mark_all_notifications_read'),
    path('logout/', student_logout, name='student_logout'),
]
