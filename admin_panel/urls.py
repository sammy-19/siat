from django.urls import path
from . import views
from .views import dashboard, register_student, register_instructor, edit_about_section, portal_settings, admin_logout
from .views_auth import AdminLoginView

app_name = 'admin_panel'
urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='admin_login'),
    path('', dashboard, name='dashboard'),
    path('register-student/', register_student, name='register_student'),
    path('register-instructor/', register_instructor, name='register_instructor'),
    path('edit-about-section/', edit_about_section, name='edit_about_section'),
    path('edit-about-section/<int:pk>/', edit_about_section, name='edit_about_section'),
    path('portal-settings/', portal_settings, name='portal_settings'),
    path('logout/', admin_logout, name='admin_logout')
    ,
    # Students
    path('students/', views.manage_students, name='manage_students'),
    path('students/<int:student_id>/edit/', views.edit_student, name='edit_student'),
    path('students/<int:pk>/delete/', views.delete_student, name='delete_student'),

    # Instructors
    path('instructors/', views.manage_instructors, name='manage_instructors'),
    path('instructors/<int:pk>/edit/', views.edit_instructor, name='edit_instructor'),
    path('instructors/<int:pk>/delete/', views.delete_instructor, name='delete_instructor'),

    # Schools
    path('schools/', views.manage_schools, name='manage_schools'),
    path('schools/add/', views.add_school, name='add_school'),
    path('schools/<int:pk>/edit/', views.edit_school, name='edit_school'),
    path('schools/<int:pk>/delete/', views.delete_school, name='delete_school'),

    # Departments
    path('departments/', views.manage_departments, name='manage_departments'),
    path('departments/add/', views.add_department, name='add_department'),
    path('departments/<int:pk>/edit/', views.edit_department, name='edit_department'),
    path('departments/<int:pk>/delete/', views.delete_department, name='delete_department'),
    
    # Subjects
    path('subjects/', views.manage_subjects, name='manage_subjects'),
    path('subjects/add/', views.add_subject, name='add_subject'),
    path('subjects/edit/<int:pk>/', views.edit_subject, name='edit_subject'),
    path('subjects/delete/<int:pk>/', views.delete_subject, name='delete_subject'),
    path('assign_subject/<int:subject_id>/', views.assign_subject_to_courses, name='assign_subject_to_courses'),
    path('subjects/assign-instructor/<int:subject_id>/', views.assign_instructor_to_course, name='assign_instructor_to_course'),
]
