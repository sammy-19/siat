from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import AboutSection, PortalSettings
from .forms import StudentRegistrationForm, InstructorRegistrationForm, AboutSectionForm, PortalSettingsForm
from student_portal.models import StudentProfile
from instructor_portal.models import InstructorProfile
from core.models import Course



def is_admin(user):
    return user.is_superuser

@login_required
@user_passes_test(is_admin, login_url='/admin_panel/login/')
def dashboard(request):
    students = StudentProfile.objects.all()
    instructors = InstructorProfile.objects.all()
    about_sections = AboutSection.objects.all()
    settings = PortalSettings.objects.first() or PortalSettings.objects.create()
    context = {
        'students': students,
        'instructors': instructors,
        'about_sections': about_sections,
        'settings': settings,
        'meta_description': 'SIAT Admin CMS Dashboard - Manage students, instructors, and content in applied sciences technology Zambia.',
    }
    return render(request, 'admin_panel/dashboard.html', context)

@login_required
def register_student(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('admin_panel:dashboard')
    else:
        form = StudentRegistrationForm()
    return render(request, 'admin_panel/register_student.html', {'form': form})

@login_required
def register_instructor(request):
    if request.method == 'POST':
        form = InstructorRegistrationForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('admin_panel:dashboard')
    else:
        form = InstructorRegistrationForm()
    return render(request, 'admin_panel/register_instructor.html', {'form': form})

@login_required
def edit_about_section(request, pk=None):
    if pk:
        section = get_object_or_404(AboutSection, pk=pk)
    else:
        section = None
    if request.method == 'POST':
        form = AboutSectionForm(request.POST, instance=section)
        if form.is_valid():
            form.save()
            return redirect('admin_panel:dashboard')
    else:
        form = AboutSectionForm(instance=section)
    return render(request, 'admin_panel/edit_about_section.html', {'form': form, 'section': section})

@login_required
def portal_settings(request):
    settings = PortalSettings.objects.first() or PortalSettings.objects.create()
    if request.method == 'POST':
        form = PortalSettingsForm(request.POST, instance=settings)
        if form.is_valid():
            form.save()
            return redirect('admin_panel:dashboard')
    else:
        form = PortalSettingsForm(instance=settings)
    return render(request, 'admin_panel/portal_settings.html', {'form': form})

def admin_logout(request):
    logout(request)  # This will remove the user session and log them out
    messages.success(request, "Successfully logged out.")
    return redirect('admin_login')