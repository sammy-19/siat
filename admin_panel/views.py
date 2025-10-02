from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from random import sample
from .models import AboutSection, PortalSettings
from student_portal.models import StudentProfile
from instructor_portal.models import InstructorProfile
from core.models import School, Department
from .forms import (
    SchoolForm, DepartmentForm,
    StudentSchoolForm, InstructorDepartmentForm, InstructorEditForm,
    StudentRegistrationForm, StudentEditForm, InstructorRegistrationForm,
    AboutSectionForm, PortalSettingsForm
)


@login_required(login_url='/admin_panel/login/')
def dashboard(request):
    if request.session.get("portal") != "admin":
        logout(request)
        return redirect("admin_panel:admin_login")
    
    # fetch all students and instructors
    students_qs = list(StudentProfile.objects.all().prefetch_related('enrollment_set__course'))
    instructors_qs = list(InstructorProfile.objects.all())

    # pick up to 3 random ones each
    students = sample(students_qs, min(len(students_qs), 3))
    instructors = sample(instructors_qs, min(len(instructors_qs), 3))
    
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
    return redirect('admin_panel:admin_login')

# -------- Manage Students ----------
@login_required(login_url='/admin_panel/login/')
def manage_students(request):
    students = StudentProfile.objects.select_related('school').all().order_by('full_name')
    return render(request, 'admin_panel/manage_students.html', {'students': students})

@login_required
def edit_student(request, student_id):
    student = get_object_or_404(StudentProfile, pk=student_id)

    if request.method == "POST":
        form = StudentEditForm(request.POST, request.FILES, instance=student)
        if form.is_valid():
            form.save()
            messages.success(request, "Student updated successfully.")
            return redirect("admin_panel:manage_students")
    else:
        form = StudentEditForm(instance=student)

    return render(request, "admin_panel/edit_student.html", {"form": form, "student": student})


@login_required(login_url='/admin_panel/login/')
def delete_student(request, pk):
    student = get_object_or_404(StudentProfile, pk=pk)
    if request.method == 'POST':
        student.delete()
        messages.success(request, "Student deleted.")
        return redirect('admin_panel:dashboard')
    return render(request, 'admin_panel/confirm_delete.html', {'object': student, 'type': 'Student'})

# -------- Manage Instructors ----------
@login_required(login_url='/admin_panel/login/')
def manage_instructors(request):
    instructors = InstructorProfile.objects.select_related('department').all().order_by('full_name')
    return render(request, 'admin_panel/manage_instructors.html', {'instructors': instructors})

@login_required(login_url='/admin_panel/login/')
def edit_instructor(request, pk):
    instructor = get_object_or_404(InstructorProfile, pk=pk)

    if request.method == 'POST':
        form = InstructorEditForm(request.POST, request.FILES, instance=instructor)
        dept_form = InstructorDepartmentForm(request.POST, instance=instructor)

        if form.is_valid() and dept_form.is_valid():
            form.save()
            dept_form.save()
            messages.success(request, "Instructor updated.")
            return redirect('admin_panel:manage_instructors')
    else:
        form = InstructorEditForm(instance=instructor)
        dept_form = InstructorDepartmentForm(instance=instructor)

    return render(request, 'admin_panel/edit_instructor.html', {
        'form': form,
        'dept_form': dept_form,
        'instructor': instructor
    })

@login_required(login_url='/admin_panel/login/')
def delete_instructor(request, pk):
    instructor = get_object_or_404(InstructorProfile, pk=pk)
    if request.method == 'POST':
        instructor.delete()
        messages.success(request, "Instructor deleted.")
        return redirect('admin_panel:dashboard')
    return render(request, 'admin_panel/confirm_delete.html', {'object': instructor, 'type': 'Instructor'})

# -------- Schools ----------
@login_required(login_url='/admin_panel/login/')
def manage_schools(request):
    schools = School.objects.all().order_by('name')
    students = StudentProfile.objects.select_related('school').all()

    # inline assignment (one row per student)
    if request.method == 'POST' and request.POST.get('assign_student') == '1':
        student_id = request.POST.get('student_id')
        school_id = request.POST.get('school_id') or None
        student = get_object_or_404(StudentProfile, pk=student_id)
        student.school_id = school_id
        student.save()
        messages.success(request, "Student assignment updated.")
        return redirect('admin_panel:manage_schools')

    return render(request, 'admin_panel/manage_schools.html', {
        'schools': schools,
        'students': students,
        'school_form': SchoolForm()
    })

@login_required(login_url='/admin_panel/login/')
def add_school(request):
    if request.method == 'POST':
        form = SchoolForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "School added.")
            return redirect('admin_panel:manage_schools')
    else:
        form = SchoolForm()
    return render(request, 'admin_panel/simple_form.html', {'form': form, 'title': 'Add School'})

@login_required(login_url='/admin_panel/login/')
def edit_school(request, pk):
    school = get_object_or_404(School, pk=pk)
    if request.method == 'POST':
        form = SchoolForm(request.POST, instance=school)
        if form.is_valid():
            form.save()
            messages.success(request, "School updated.")
            return redirect('admin_panel:manage_schools')
    else:
        form = SchoolForm(instance=school)
    return render(request, 'admin_panel/simple_form.html', {'form': form, 'title': f'Edit School: {school.name}'})

@login_required(login_url='/admin_panel/login/')
def delete_school(request, pk):
    school = get_object_or_404(School, pk=pk)
    if request.method == 'POST':
        school.delete()
        messages.success(request, "School deleted.")
        return redirect('admin_panel:manage_schools')
    return render(request, 'admin_panel/confirm_delete.html', {'object': school, 'type': 'School'})

# -------- Departments ----------
@login_required(login_url='/admin_panel/login/')
def manage_departments(request):
    departments = Department.objects.select_related('school').all().order_by('school__name', 'name')
    instructors = InstructorProfile.objects.select_related('department').all()

    if request.method == 'POST' and request.POST.get('assign_instructor') == '1':
        instructor_id = request.POST.get('instructor_id')
        dept_id = request.POST.get('department_id') or None
        instructor = get_object_or_404(InstructorProfile, pk=instructor_id)
        instructor.department_id = dept_id
        instructor.save()
        messages.success(request, "Instructor assignment updated.")
        return redirect('admin_panel:manage_departments')

    return render(request, 'admin_panel/manage_departments.html', {
        'departments': departments,
        'instructors': instructors,
        'department_form': DepartmentForm()
    })

@login_required(login_url='/admin_panel/login/')
def add_department(request):
    if request.method == 'POST':
        form = DepartmentForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Department added.")
            return redirect('admin_panel:manage_departments')
    else:
        form = DepartmentForm()
    return render(request, 'admin_panel/simple_form.html', {'form': form, 'title': 'Add Department'})

@login_required(login_url='/admin_panel/login/')
def edit_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        form = DepartmentForm(request.POST, instance=department)
        if form.is_valid():
            form.save()
            messages.success(request, "Department updated.")
            return redirect('admin_panel:manage_departments')
    else:
        form = DepartmentForm(instance=department)
    return render(request, 'admin_panel/simple_form.html', {'form': form, 'title': f'Edit Department: {department.name}'})

@login_required(login_url='/admin_panel/login/')
def delete_department(request, pk):
    department = get_object_or_404(Department, pk=pk)
    if request.method == 'POST':
        department.delete()
        messages.success(request, "Department deleted.")
        return redirect('admin_panel:manage_departments')
    return render(request, 'admin_panel/confirm_delete.html', {'object': department, 'type': 'Department'})
