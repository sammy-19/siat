from django.shortcuts import render, redirect, get_object_or_404
from core.models import Course
from student_portal.models import StudentProfile, Enrollment, LearningMaterial, Assignment, Submission
from .models import InstructorProfile
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required, user_passes_test
import logging


logger = logging.getLogger(__name__)

def is_instructor(user):
    return user.groups.filter(name='Instructor').exists()

@login_required
@user_passes_test(is_instructor, login_url='/instructor_portal/login/')
def dashboard(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    courses = profile.courses_taught.all()
    for course in courses:
        enrollments = Enrollment.objects.filter(course=course)
        num_enrolled = enrollments.count()
    context = {
        'profile': profile,
        'courses': courses,
        'num_enrolled': num_enrolled,
        'meta_description': 'SIAT Instructor Portal Dashboard - Manage materials, assignments, and students.',
    }
    return render(request, 'instructor_portal/dashboard.html', context)

@login_required
def materials(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    courses = profile.courses_taught.all()
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        title = request.POST.get('title')
        file = request.FILES.get('file')
        material_type = request.POST.get('type', 'module')
        if not title or not file:
            messages.error(request, "Title and file are required.")
            return render(request, 'instructor_portal/materials.html', {'courses': courses})
        allowed_types = ['application/pdf', 'video/mp4']
        if file.content_type not in allowed_types:
            messages.error(request, "Only PDF and MP4 files are allowed.")
            return render(request, 'instructor_portal/materials.html', {'courses': courses})
        try:
            upload_result = upload(file, resource_type='auto')
            material_url = upload_result.get('secure_url')
            LearningMaterial.objects.create(
                course=course,
                title=title,
                file=material_url,
                type=material_type
            )
            messages.success(request, "Material uploaded successfully.")
        except Exception as e:
            logger.error(f"Upload failed: {str(e)}")
            messages.error(request, f"Failed to upload material: {str(e)}")
        return redirect('instructor_portal:materials')
    materials = LearningMaterial.objects.filter(course__in=courses).order_by('-created_at')
    context = {
        'courses': courses,
        'materials': materials,
        'meta_description': 'SIAT Instructor Portal - Manage course materials like PDFs and videos.',
    }
    return render(request, 'instructor_portal/materials.html', context)

@login_required
def assignments(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    courses = profile.courses_taught.all()
    assignments = Assignment.objects.filter(course__in=courses)
    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        file = request.FILES.get('file')
        if not title or not description or not due_date:
            messages.error(request, "All fields are required.")
            return render(request, 'instructor_portal/assignments.html', {'courses': courses})
        try:
            assignment_data = {'course': course, 'title': title, 'description': description, 'due_date': due_date}
            if file:
                upload_result = upload(file, resource_type='raw')
                assignment_data['file'] = upload_result.get('secure_url')
                assignment_data['file_public_id'] = upload_result.get('public_id')
                Assignment.objects.create(**assignment_data)
            messages.success(request, "Assignment created successfully.")
        except Exception as e:
            logger.error(f"Assignment creation failed: {str(e)}")
            messages.error(request, f"Failed to create assignment: {str(e)}")
        return redirect('instructor_portal:assignments')
    # In views.py, assignments view
    # try:
    #     if file:
    #         # upload_result = upload(file, resource_type='raw', public_id=f'assignments/{title}_{course.id}')
    #         assignment_data['file'] = upload_result.get('secure_url')
    # except Exception as e:
    #     logger.error(f"Cloudinary upload failed: {str(e)}")
    #     messages.error(request, f"Upload failed: {str(e)}")
    context = {
        'courses': courses,
        'assignments': assignments,
        'meta_description': 'SIAT Instructor Portal - Create and manage assignments.',
    }
    return render(request, 'instructor_portal/assignments.html', context)

@login_required
def download_pdf(request, assignment_id):
    assignment = get_object_or_404(Assignment, id=assignment_id)
    if not assignment.file_public_id:
        messages.error(request, "No file available for download.")
        return redirect('instructor_portal:assignments')

    # Generate correct raw resource URL
    url, options = cloudinary_url(
        assignment.file_public_id,
        resource_type='raw',
        type='upload',
    )
    return redirect(url)

@login_required
def submissions(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    courses = profile.courses_taught.all()
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        grade = request.POST.get('grade')
        if submission_id and grade:
            submission = get_object_or_404(Submission, id=submission_id)
            submission.grade = grade
            submission.save()
            messages.success(request, "Grade updated successfully.")
        return redirect('instructor_portal:submissions')
    submissions = Submission.objects.filter(assignment__course__in=courses).order_by('-submitted_at')
    context = {
        'courses': courses,
        'submissions': submissions,
        'meta_description': 'SIAT Instructor Portal - Review and grade student submissions.',
    }
    return render(request, 'instructor_portal/submissions.html', context)

@login_required
def grading(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    courses = profile.courses_taught.all()
    if request.method == 'POST':
        for course in courses:
            enrollments = Enrollment.objects.filter(course=course)
            for enrollment in enrollments:
                grade = request.POST.get(f'grade_{enrollment.id}')
                if grade:
                    enrollment.grade = grade
                    enrollment.save()
        messages.success(request, "Grades updated successfully.")
        return redirect('instructor_portal:grading')
    context = {
        'courses': courses,
        'meta_description': 'SIAT Instructor Portal - Grade students for taught courses.',
    }
    return render(request, 'instructor_portal/grading.html', context)

@login_required
def monitoring(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    courses = profile.courses_taught.all()
    enrollments = Enrollment.objects.filter(course__in=courses)
    num_enrolled = enrollments.count()
    context = {
        'courses': courses,
        'enrollments': enrollments,
        'num_enrolled': num_enrolled,
        'meta_description': 'SIAT Instructor Portal - Monitor student progress in taught courses.',
    }
    return render(request, 'instructor_portal/monitoring.html', context)

def instructor_logout(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('instructor_login')