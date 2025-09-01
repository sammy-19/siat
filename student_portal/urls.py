from django.urls import path
from .views import dashboard, profile, courses, assignments, materials, student_logout, semester, download_pdf, CourseDetailView, AssignmentDetailView

app_name = 'student_portal'

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('profile/', profile, name='profile'),
    path('courses/', courses, name='courses'),
    path('assignments/', assignments, name='assignments'),
    path('materials/', materials, name='materials'),
    path('semester/', semester, name='semester'),
    path('course/<int:pk>/', CourseDetailView.as_view(), name='course_detail'),
    path('assignment/<int:pk>/', AssignmentDetailView.as_view(), name='assignment_detail'),
    path('download/<int:assignment_id>/', download_pdf, name='download_pdf'),
    path('logout/', student_logout, name='student_logout'),
]