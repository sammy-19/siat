from django.shortcuts import render, redirect, get_object_or_404
from core.models import Course
from student_portal.models import (
    SubjectEnrollment, LearningMaterial, Assignment, Submission, 
    CourseSubject, Semester, Subject, Notification, StudentProfile
)
from .models import InstructorProfile
from cloudinary.uploader import upload
from cloudinary.utils import cloudinary_url
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Avg
import logging
from .forms import CourseSubjectForm


MAX_UPLOAD_SIZE_MB = 4.5
MAX_UPLOAD_SIZE = MAX_UPLOAD_SIZE_MB * 1024 * 1024


logger = logging.getLogger(__name__)


@login_required(login_url='/instructor/login/')
def dashboard(request):
    if request.session.get("portal") != "instructor":
        logout(request)
        return redirect("instructor_portal:instructor_login")
    
    profile = get_object_or_404(InstructorProfile, user=request.user)
    
    # Get subjects assigned to this instructor
    current_semester = Semester.objects.filter(is_current=True).first()
    course_subjects = CourseSubject.objects.filter(
        instructor=profile,
        semester=current_semester
    ).select_related('course', 'subject', 'semester')
    
    subjects = Subject.objects.filter(
        id__in=course_subjects.values_list('subject_id', flat=True)
    ).annotate(
        num_enrolled=Count('coursesubject__enrollments'),
        avg_score=Avg('assignments__submission__score')
    )

    # Get 3 latest submissions for subjects this instructor teaches
    latest_submissions = Submission.objects.filter(
        assignment__subject__in=subjects
    ).select_related('student', 'assignment').order_by('-submitted_at')[:3]

    context = {
        'profile': profile,
        'subjects': subjects,
        'course_subjects': course_subjects,
        'latest_submissions': latest_submissions,
        'meta_description': 'SIAT Instructor Portal Dashboard - Manage materials, assignments, and students.',
    }
    return render(request, 'instructor_portal/dashboard.html', context)

@login_required(login_url='/instructor/login/')
def materials(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    course_subjects = CourseSubject.objects.filter(
        instructor=profile,
        semester=current_semester
    ).select_related('subject')
    subjects = Subject.objects.filter(id__in=course_subjects.values_list('subject_id', flat=True))

    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        subject = get_object_or_404(Subject, id=subject_id)
        title = request.POST.get('title')
        material_type = request.POST.get('type', 'module')

        file = request.FILES.get('file')
        video_url = request.POST.get('video_url')

        if not title:
            messages.error(request, "Title is required.")
            return redirect('instructor_portal:materials')

        try:
            if material_type == 'video':
                if not video_url:
                    messages.error(request, "Please provide a YouTube link for video materials.")
                    return redirect('instructor_portal:materials')
                # Enforce YouTube-only URLs
                url_l = video_url.lower()
                is_youtube = (
                    url_l.startswith('https://www.youtube.com/watch') or
                    url_l.startswith('http://www.youtube.com/watch') or
                    url_l.startswith('https://youtube.com/watch') or
                    url_l.startswith('http://youtube.com/watch') or
                    url_l.startswith('https://youtu.be/') or
                    url_l.startswith('http://youtu.be/')
                )
                if not is_youtube:
                    messages.error(request, "Only YouTube links are allowed for video materials (e.g., https://www.youtube.com/watch?v=... or https://youtu.be/...).")
                    return redirect('instructor_portal:materials')
                material = LearningMaterial.objects.create(
                    subject=subject, title=title, type='video', video_url=video_url
                )
                
                course_ids = CourseSubject.objects.filter(
                    subject=subject,
                    semester__is_current=True
                ).values_list('course_id', flat=True)
                
                students = StudentProfile.objects.filter(
                    enrollment__course_id__in=course_ids
                ).distinct()
                
                for student in students:
                    Notification.objects.create(
                        student=student,
                        type='material',
                        title=f'New Material: {title}',
                        message=f'A new video has been uploaded for {subject.title}',
                        link=f'/portal/materials/?subject_id={subject.id}'
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
                material = LearningMaterial.objects.create(
                    subject=subject, title=title, type=material_type, file=upload_result.get('secure_url')
                )
                
                course_ids = CourseSubject.objects.filter(
                    subject=subject,
                    semester__is_current=True
                ).values_list('course_id', flat=True)
                
                students = StudentProfile.objects.filter(
                    enrollment__course_id__in=course_ids
                ).distinct()
                
                for student in students:
                    Notification.objects.create(
                        student=student,
                        type='material',
                        title=f'New Material: {title}',
                        message=f'A new {material_type} has been uploaded for {subject.title}',
                        link=f'/portal/materials/?subject_id={subject.id}'
                    )
                
                messages.success(request, "Material uploaded successfully.")
        except Exception as e:
            logger.error(f"Material upload failed: {str(e)}")
            messages.error(request, f"Failed to upload material: {str(e)}")

        return redirect('instructor_portal:materials')

    materials = LearningMaterial.objects.filter(subject__in=subjects).order_by('-created_at')
    return render(request, 'instructor_portal/materials.html', {
        'subjects': subjects,
        'materials': materials
    })

@login_required(login_url='/instructor/login/')
def assignments(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    course_subjects = CourseSubject.objects.filter(
        instructor=profile,
        semester=current_semester
    ).select_related('subject')
    subjects = Subject.objects.filter(id__in=course_subjects.values_list('subject_id', flat=True))
    assignments = Assignment.objects.filter(subject__in=subjects)
    
    if request.method == 'POST':
        subject_id = request.POST.get('subject_id')
        subject = get_object_or_404(Subject, id=subject_id)
        title = request.POST.get('title')
        description = request.POST.get('description')
        due_date = request.POST.get('due_date')
        file = request.FILES.get('file')
        if not title or not description or not due_date:
            messages.error(request, "All fields are required.")
            return render(request, 'instructor_portal/assignments.html', {'subjects': subjects})
        try:
            assignment_data = {'subject': subject, 'title': title, 'description': description, 'due_date': due_date}
            if file:
                if file.size > MAX_UPLOAD_SIZE:
                    messages.error(request, f"File too large. Max allowed is {MAX_UPLOAD_SIZE_MB}MB. Your file: {file.size/1024/1024:.2f}MB")
                    return redirect('instructor_portal:assignments')
                
                upload_result = upload(file, resource_type='raw')
                assignment_data['file'] = upload_result.get('secure_url')
                assignment_data['file_public_id'] = upload_result.get('public_id')
            
            assignment = Assignment.objects.create(**assignment_data)
            
            course_ids = CourseSubject.objects.filter(
                subject=subject,
                semester__is_current=True
            ).values_list('course_id', flat=True)
            
            students = StudentProfile.objects.filter(
                enrollment__course_id__in=course_ids
            ).distinct()
            
            for student in students:
                Notification.objects.create(
                    student=student,
                    type='assignment',
                    title=f'New Assignment: {title}',
                    message=f'A new assignment has been posted for {subject.title}. Due: {due_date}',
                    link='/portal/assignments/'
                )
            
            messages.success(request, "Assignment created successfully.")
        except Exception as e:
            logger.error(f"Assignment creation failed: {str(e)}")
            messages.error(request, f"Failed to create assignment: {str(e)}")
        return redirect('instructor_portal:assignments')

    context = {
        'subjects': subjects,
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
    current_semester = Semester.objects.filter(is_current=True).first()
    course_subjects = CourseSubject.objects.filter(
        instructor=profile,
        semester=current_semester
    ).select_related('subject')
    subjects = Subject.objects.filter(id__in=course_subjects.values_list('subject_id', flat=True))
    
    if request.method == 'POST':
        submission_id = request.POST.get('submission_id')
        grade = request.POST.get('grade')
        score = request.POST.get('score')
        if submission_id:
            submission = get_object_or_404(Submission, id=submission_id)
            if grade:
                submission.grade = grade
            if score:
                try:
                    score_int = int(score)
                    if 0 <= score_int <= 100:
                        submission.score = score_int
                    else:
                        messages.error(request, "Score must be between 0 and 100.")
                        return redirect('instructor_portal:submissions')
                except ValueError:
                    messages.error(request, "Invalid score value.")
                    return redirect('instructor_portal:submissions')
            submission.save()
            messages.success(request, "Submission updated successfully.")
        return redirect('instructor_portal:submissions')
    
    submissions = Submission.objects.filter(assignment__subject__in=subjects).order_by('-submitted_at')
    context = {
        'subjects': subjects,
        'submissions': submissions,
        'meta_description': 'SIAT Instructor Portal - Review and grade student submissions.',
    }
    return render(request, 'instructor_portal/submissions.html', context)

@login_required(login_url='/instructor/login/')
def grading(request):
    from student_portal.models import Enrollment
    
    profile = get_object_or_404(InstructorProfile, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    course_subjects = CourseSubject.objects.filter(
        instructor=profile,
        semester=current_semester
    ).select_related('subject', 'course', 'semester')
    
    for cs in course_subjects:
        course_enrollments = Enrollment.objects.filter(course=cs.course).select_related('student')
        
        for enrollment in course_enrollments:
            subject_enrollment, created = SubjectEnrollment.objects.get_or_create(
                student=enrollment.student,
                course_subject=cs
            )
        
        cs.student_enrollments = SubjectEnrollment.objects.filter(
            course_subject=cs
        ).select_related('student')
    
    if request.method == 'POST':
        for course_subject in course_subjects:
            enrollments = SubjectEnrollment.objects.filter(course_subject=course_subject)
            for enrollment in enrollments:
                grade = request.POST.get(f'grade_{enrollment.id}')
                final_score = request.POST.get(f'score_{enrollment.id}')
                if grade:
                    enrollment.grade = grade
                if final_score:
                    try:
                        score_int = int(final_score)
                        if 0 <= score_int <= 100:
                            enrollment.final_score = score_int
                        else:
                            continue
                    except ValueError:
                        continue
                enrollment.save()
        messages.success(request, "Grades updated successfully.")
        return redirect('instructor_portal:grading')
    
    context = {
        'course_subjects': course_subjects,
        'meta_description': 'SIAT Instructor Portal - Grade students for taught subjects.',
    }
    return render(request, 'instructor_portal/grading.html', context)

@login_required(login_url='/instructor/login/')
def monitoring(request):
    from student_portal.models import Enrollment
    
    profile = get_object_or_404(InstructorProfile, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    course_subjects = CourseSubject.objects.filter(
        instructor=profile,
        semester=current_semester
    ).select_related('subject', 'course')
    
    for cs in course_subjects:
        course_enrollments = Enrollment.objects.filter(course=cs.course).select_related('student')
        
        for enrollment in course_enrollments:
            subject_enrollment, created = SubjectEnrollment.objects.get_or_create(
                student=enrollment.student,
                course_subject=cs
            )
    
    enrollments = SubjectEnrollment.objects.filter(
        course_subject__in=course_subjects
    ).select_related('student', 'course_subject__subject')
    
    num_enrolled = enrollments.count()
    
    context = {
        'course_subjects': course_subjects,
        'enrollments': enrollments,
        'num_enrolled': num_enrolled,
        'meta_description': 'SIAT Instructor Portal - Monitor student progress in taught subjects.',
    }
    return render(request, 'instructor_portal/monitoring.html', context)

@login_required(login_url='/instructor/login/')
def assign_subjects(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    if request.method == "POST":
        form = CourseSubjectForm(request.POST, user=request.user)
        if form.is_valid():
            course_subject = form.save(commit=False)
            course_subject.instructor = profile
            course_subject.save()
            messages.success(request, f"Subject '{course_subject.subject.title}' assigned successfully!")
            return redirect("instructor_portal:manage_subjects")
    else:
        form = CourseSubjectForm(user=request.user)

    return render(request, "instructor_portal/assign_subjects.html", {"form": form})

@login_required(login_url='/instructor/login/')
def manage_subjects(request):
    profile = get_object_or_404(InstructorProfile, user=request.user)
    current_semester = Semester.objects.filter(is_current=True).first()
    subjects = CourseSubject.objects.filter(instructor=profile, semester=current_semester)

    return render(request, "instructor_portal/manage_subjects.html", {
        "subjects": subjects,
        "semester": current_semester,
    })

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
