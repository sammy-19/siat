"""
URL configuration for siat project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from core import views as core_views

urlpatterns = [
    path('admin/', admin.site.urls),  # Assuming custom admin from previous context (if used)
    path('', core_views.home, name='home'),
    path('about/', core_views.about, name='about'),
    path('courses/', core_views.courses, name='courses'),
    path('courses/<slug:slug>/', core_views.course_detail, name='course_detail'),
    path('enroll/', core_views.enroll, name='enroll'),
    path('enroll/<slug:course_slug>/', core_views.enroll, name='enroll_course'),
    path('thank-you/', core_views.thank_you, name='thank_you'),
    path('contact/', core_views.contact, name='contact'),
    path('portal/', include('student_portal.urls')),
    path('instructor/', include('instructor_portal.urls')),
    
    path('accounts/login/', auth_views.LoginView.as_view(template_name='login.html', ), name='account_login'),  # New pattern
    #path('login/', auth_views.LoginView.as_view(template_name='login.html', redirect_authenticated_user=True), name='login'),  # General login
    path('instructor/login/', auth_views.LoginView.as_view(
        template_name='instructor_portal/login.html', 
        redirect_authenticated_user=True,
        extra_context={'next': '/instructor/'}), 
        name='instructor_login'),
    
    path('portal/login/', auth_views.LoginView.as_view(
        template_name='student_portal/login.html',
        redirect_authenticated_user=True,
        extra_context={'next': '/portal/'}
        ), 
        name='student_login'),
    
    path('admin_panel/login/', auth_views.LoginView.as_view(
        template_name='admin_panel/login.html', 
        redirect_authenticated_user=True,
        extra_context={'next': '/admin_panel/'}),
        name='admin_login'),
    
    path('admin_panel/', include('admin_panel.urls')),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)