from django.urls import path
from .views import dashboard, materials, assignments, submissions, grading, monitoring, instructor_logout, download_pdf

app_name = 'instructor_portal'
urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('materials/', materials, name='materials'),
    path('assignments/', assignments, name='assignments'),
    path('submissions/', submissions, name='submissions'),
    path('grading/', grading, name='grading'),
    path('monitoring/', monitoring, name='monitoring'),
    path('logout/', instructor_logout, name='instructor_logout'),
    path('download/<int:assignment_id>/', download_pdf, name='download_pdf'),
]