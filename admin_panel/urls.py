from django.urls import path
from .views import dashboard, register_student, register_instructor, edit_about_section, portal_settings, admin_logout

app_name = 'admin_panel'
urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('register-student/', register_student, name='register_student'),
    path('register-instructor/', register_instructor, name='register_instructor'),
    path('edit-about-section/', edit_about_section, name='edit_about_section'),
    path('edit-about-section/<int:pk>/', edit_about_section, name='edit_about_section'),
    path('portal-settings/', portal_settings, name='portal_settings'),
    path('logout/', admin_logout, name='admin_logout'),
]