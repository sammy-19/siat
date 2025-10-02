from django.shortcuts import render, redirect, get_object_or_404
from core.models import Course
from student_portal.models import StudentProfile, Enrollment, LearningMaterial, Assignment, Submission
from .models import InstructorProfile
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
import logging


MAX_UPLOAD_SIZE_MB = 4.5
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024


logger = logging.getLogger(__name__)


@login_required(login_url='/instructor/login/')
def dashboard(request):
    if request.session.get("portal") != "instructor":
        logout(request)
        return redirect("instructor_portal:instructor_login")
    
    profile = get_object_or_404(InstructorProfile, user=request.user)
    
    courses = profile.courses_taught.annotate(
        num_enrolled=Count('enrollment'),
        avg_score=Avg('assignment__submission__score')
    )

    # Get 3 latest submissions for a quick view
    latest_submissions = Submission.objects.filter(
        assignment__course__in=courses
    ).select_related('student', 'assignment').order_by('-submitted_at')[:3]

    context = {
        'profile': profile,
        'courses': courses,
        'latest_submissions': latest_submissions,
        'meta_description': 'SIAT Instructor Portal Dashboard - Manage materials, assignments, and students.',
    }
    return render(request, 'instructor_portal/dashboard.html', context)

@login_required(login_url='/instructor/login/')
def materials(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    courses = profile.courses_taught.all()

    if request.method == 'POST':
        course_id = request.POST.get('course_id')
        course = get_object_or_404(Course, id=course_id)
        title = request.POST.get('title')
        material_type = request.POST.get('type', 'module')

        file = request.FILES.get('file')
        video_url = request.POST.get('video_url')

        if not title:
            messages.error(request, "Title is required.")
            return redirect('instructor_portal:materials')

        if material_type == 'video':
            if not video_url:
                messages.error(request, "Please provide a YouTube link for video materials.")
                return redirect('instructor_portal:materials')
            LearningMaterial.objects.create(
                course=course, title=title, type='video', video_url=video_url
            )
            messages.success(request, "Video link saved successfully.")
        else:
            if not file:
                messages.error(request, "Please upload a PDF file.")
                return redirect('instructor_portal:materials')

            if file.size > MAX_UPLOAD_SIZE:
                messages.error(request, f"File too large. Max allowed is {MAX_UPLOAD_SIZE_MB}MB. Your file: {file.size/1024/1024:.2f}MB")
                return redirect('instructor_portal:materials')

            upload_result = upload(file, resource_type='raw')
            LearningMaterial.objects.create(
                course=course, title=title, type=material_type, file=upload_result.get('secure_url')
            )
            messages.success(request, "Material uploaded successfully.")

        return redirect('instructor_portal:materials')

    materials = LearningMaterial.objects.filter(course__in=courses).order_by('-created_at')
    return render(request, 'instructor_portal/materials.html', {
        'courses': courses,
        'materials': materials
    })

@login_required(login_url='/instructor/login/')
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
                if file and file.size > MAX_UPLOAD_SIZE:
                    messages.error(request, f"File too large. Max allowed is {MAX_UPLOAD_SIZE_MB}MB. Your file: {file.size/1024/1024:.2f}MB")
                    return redirect('instructor_portal:assignments')
                
                upload_result = upload(file, resource_type='raw')
                assignment_data['file'] = upload_result.get('secure_url')
                assignment_data['file_public_id'] = upload_result.get('public_id')
                Assignment.objects.create(**assignment_data)
            messages.success(request, "Assignment created successfully.")
        except Exception as e:
            logger.error(f"Assignment creation failed: {str(e)}")
            messages.error(request, f"Failed to create assignment: {str(e)}")
        return redirect('instructor_portal:assignments')

    context = {
        'courses': courses,
        'assignments': assignments,
        'meta_description': 'SIAT Instructor Portal - Create and manage assignments.',
    }
    return render(request, 'instructor_portal/assignments.html', context)

@login_required(login_url='/instructor/login/')
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

@login_required(login_url='/instructor/login/')
def submissions(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    courses = profile.courses_taught.all()
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        grade = request.POST.get('grade')
        score = request.POST.get('score')
        if submission_id:
            submission = get_object_or_404(Submission, id=submission_id)
            if grade:
                submission.grade = grade
            if score:
                submission.score = int(score)
            submission.save()
            messages.success(request, "Submission updated successfully.")
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

@login_required(login_url='/instructor/login/')
def delete_assignment(request, pk):
    assignment = get_object_or_404(Assignment, pk=pk)
    assignment.delete()
    messages.success(request, "Assignment deleted successfully.")
    return redirect('instructor_portal:assignments')

def instructor_logout(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('instructor_portal:instructor_login')