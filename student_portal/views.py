from django.shortcuts import render, redirect, get_object_or_404
from django.http import Http404
from django.views.generic import DetailView
from .models import Enrollment, Assignment, Submission, CourseSubject, LearningMaterial, Semester, StudentProfile, NotificationPreference, Announcement
from .forms import SubmissionForm, ProfileForm
from core.models import Course
from django.db import models
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
import logging
from cloudinary.utils import cloudinary_url


logger = logging.getLogger(__name__)

@login_required(login_url='/portal/login/')
def dashboard(request):
    if request.session.get("portal") != "student":
        logout(request)
        return redirect("student_portal:student_login")
    
    profile = get_object_or_404(StudentProfile, user=request.user)
    enrollments = Enrollment.objects.filter(student=profile)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get subjects for the student's current semester and enrolled courses
    if current_semester:
        course_subjects = CourseSubject.objects.filter(
            course__in=enrollments.values_list('course', flat=True),
            semester=current_semester,
            is_active=True
        ).select_related('subject', 'course')
    else:
        course_subjects = []

    # Subject-level aggregates for current semester
    subject_cards = []
    course_labels = []
    avg_scores = []
    if current_semester:
        subjects_qs = CourseSubject.objects.filter(
            course__in=enrollments.values_list('course', flat=True),
            semester=current_semester,
            is_active=True
        ).select_related('subject', 'course').values('subject_id', 'subject__title').distinct()
        for s in subjects_qs:
            subject_id = s['subject_id']
            subject_title = s['subject__title']
            subject_course_ids = CourseSubject.objects.filter(
                subject_id=subject_id, semester=current_semester, is_active=True,
                course__in=enrollments.values_list('course', flat=True)
            ).values_list('course_id', flat=True)

            # Get SubjectEnrollment for progress tracking
            from .models import SubjectEnrollment
            subject_enrollment = SubjectEnrollment.objects.filter(
                student=profile,
                course_subject__subject_id=subject_id,
                course_subject__semester=current_semester
            ).first()
            
            subj_avg_score = Submission.objects.filter(
                assignment__subject_id=subject_id,
                student=profile
            ).aggregate(avg=models.Avg('score'))['avg'] or 0
            
            subj_progress = subject_enrollment.progress if subject_enrollment else 0
            subj_assignments = Assignment.objects.filter(subject_id=subject_id).count()
            subj_materials = LearningMaterial.objects.filter(subject_id=subject_id).count()

            subject_cards.append({
                'id': subject_id,
                'title': subject_title,
                'avg_score': round(subj_avg_score, 2) if subj_avg_score else 0,
                'avg_progress': round(subj_progress, 2) if subj_progress else 0,
                'assignments_count': subj_assignments,
                'materials_count': subj_materials,
            })
            course_labels.append(subject_title)
            avg_scores.append(round(subj_avg_score or 0, 2))
    
    # Get overall progress from SubjectEnrollments
    from .models import SubjectEnrollment
    overall_progress = SubjectEnrollment.objects.filter(
        student=profile,
        course_subject__semester=current_semester
    ).aggregate(avg_progress=models.Avg('progress'))['avg_progress'] or 0
    
    notification_pref = NotificationPreference.objects.get_or_create(student=profile)[0]
    if request.GET.get('toggle_notifications'):
        notification_pref.enabled = not notification_pref.enabled
        notification_pref.save()
        return redirect('student_portal:dashboard')

    # Get announcements for subjects the student is enrolled in
    subject_ids = subjects_qs.values_list('subject_id', flat=True) if current_semester else []
    announcements = Announcement.objects.filter(subject_id__in=subject_ids).order_by('-created_at')[:5] if subject_ids else []

    # Overall average score
    overall_avg_score = sum(avg_scores) / len(avg_scores) if avg_scores else 0

    # Convert to JSON for chart
    import json
    course_labels_json = json.dumps(course_labels)
    avg_scores_json = json.dumps(avg_scores)

    context = {
        'profile': profile,
        'enrollments': enrollments,
        'overall_progress': overall_progress,
        'avg_score': overall_avg_score,
        'course_labels': course_labels_json,
        'semester':current_semester,
        'course_subjects':course_subjects,
        'subject_cards': subject_cards,
        'avg_scores': avg_scores_json,
        'notification_pref': notification_pref,
        'announcements': announcements,
        'meta_description': 'SIAT Student Portal Dashboard - Track progress, grades, scores, and notifications.',
    }
    return render(request, 'student_portal/dashboard.html', context)

@login_required(login_url='/portal/login/')
def profile(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    if request.method == 'POST':
        form = ProfileForm(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            return redirect('student_portal:profile')
    else:
        form = ProfileForm(instance=profile)
    return render(request, 'student_portal/profile.html', {'form': form, 'profile': profile})

@login_required(login_url='/portal/login/')
def courses(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    enrollments = Enrollment.objects.filter(student=profile)
        
    return render(request, 'student_portal/courses.html', {'enrollments': enrollments})

@login_required(login_url='/portal/login/')
def assignments(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    enrollments = Enrollment.objects.filter(student=profile)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    # Get subjects for enrolled courses in current semester
    if current_semester:
        subject_ids = CourseSubject.objects.filter(
            course__in=enrollments.values_list('course', flat=True),
            semester=current_semester,
            is_active=True
        ).values_list('subject_id', flat=True)
        assignments = Assignment.objects.filter(subject_id__in=subject_ids).order_by('-due_date')
    else:
        assignments = Assignment.objects.none()
    
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = get_object_or_404(Assignment, id=request.POST['assignment_id'])
            submission.student = profile
            submission.save()
            messages.success(request, "Assignment submitted successfully!")
            return redirect('student_portal:assignments')
    else:
        form = SubmissionForm()
    return render(request, 'student_portal/assignments.html', {'assignments': assignments, 'form': form})

@login_required(login_url='/portal/login/')
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

@login_required(login_url='/portal/login/')
def materials(request):
    profile = get_object_or_404(StudentProfile, user=request.user)
    enrollments = Enrollment.objects.filter(student=profile)
    current_semester = Semester.objects.filter(is_current=True).first()
    
    if not enrollments.exists() or not current_semester:
        logger.warning(f"No enrollments or semester found for student {profile.user.username}")
        materials = LearningMaterial.objects.none()  # Empty queryset
    else:
        # Get subjects for enrolled courses in current semester
        subject_ids = CourseSubject.objects.filter(
            course__in=enrollments.values_list('course', flat=True),
            semester=current_semester,
            is_active=True
        ).values_list('subject_id', flat=True)
        
        materials = LearningMaterial.objects.filter(subject_id__in=subject_ids).order_by('-created_at')
        if not materials.exists():
            logger.warning(f"No materials found for subjects {list(subject_ids)} for student {profile.user.username}")

    # Group by type for display
    materials_by_type = {
        'outline': materials.filter(type='outline'),
        'module': materials.filter(type='module'),
        'video': materials.filter(type='video'),
    }
    context = {
        'materials_by_type': materials_by_type,
        'meta_description': 'SIAT Student Portal - Access course outlines, modules, and videos for applied sciences technology Zambia/Kenya.',
    }
    return render(request, 'student_portal/materials.html', context)

@login_required(login_url='/portal/login/')
def subject_detail(request, pk):
    from .models import Subject, SubjectEnrollment
    
    # Get the subject and its course relationships
    try:
        subject = Subject.objects.get(id=pk)
    except Subject.DoesNotExist:
        raise Http404("Subject not found.")
    
    course_subjects = CourseSubject.objects.filter(
        subject=subject,
        semester__is_current=True
    ).select_related('course', 'instructor', 'subject')

    if not course_subjects.exists():
        raise Http404("No subject found for current semester.")

    # Get assignments and materials for this subject
    subject_instance = course_subjects.first()
    assignments = Assignment.objects.filter(subject=subject).order_by('-created_at')
    materials = LearningMaterial.objects.filter(subject=subject).order_by('-created_at')

    # Compute performance/progress for this subject for the logged-in student
    profile = get_object_or_404(StudentProfile, user=request.user)
    
    # Get student's subject enrollment
    subject_enrollment = SubjectEnrollment.objects.filter(
        student=profile,
        course_subject__subject=subject,
        course_subject__semester__is_current=True
    ).first()
    
    subj_avg_score = Submission.objects.filter(
        assignment__subject=subject,
        student=profile
    ).aggregate(avg=models.Avg('score'))['avg'] or 0
    
    subj_progress = subject_enrollment.progress if subject_enrollment else 0

    return render(request, 'student_portal/subject_detail.html', {
        'subject_instance': subject_instance,
        'course_subjects': course_subjects,
        'subject_enrollment': subject_enrollment,
        'assignments': assignments,
        'materials': materials,
        'subject_avg_score': round(subj_avg_score, 2) if subj_avg_score else 0,
        'subject_avg_progress': round(subj_progress, 2) if subj_progress else 0,
    }) 

@login_required(login_url='/portal/login/')
def semester(request):
    current_semester = Semester.objects.filter(is_current=True).first()
    return render(request, 'student_portal/semester.html', {'semester': current_semester})

class CourseDetailView(DetailView):
    model = Course
    template_name = 'student_portal/course_detail.html'
    context_object_name = 'course'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = StudentProfile.objects.get(user=self.request.user)
        current_semester = Semester.objects.filter(is_current=True).first()

        if current_semester:
            course_subjects = CourseSubject.objects.filter(
                course=self.object,
                semester=current_semester,
                is_active=True
            ).select_related('subject', 'course')
            
            # Get subjects for this course
            subject_ids = course_subjects.values_list('subject_id', flat=True)
            materials = LearningMaterial.objects.filter(subject_id__in=subject_ids).order_by('-created_at')
            assignments = Assignment.objects.filter(subject_id__in=subject_ids).order_by('-created_at')
        else:
            course_subjects = []
            materials = LearningMaterial.objects.none()
            assignments = Assignment.objects.none()
        
        materials_by_type = {
            'outline': materials.filter(type='outline'),
            'module': materials.filter(type='module'),
            'video': materials.filter(type='video'),
        }
        context['enrollment'] = Enrollment.objects.filter(student=profile, course=self.object).first()
        context['assignments'] = assignments
        context['course_subjects'] = course_subjects
        context['materials_by_type'] = materials_by_type
        return context

class AssignmentDetailView(DetailView):
    model = Assignment
    template_name = 'student_portal/assignment_detail.html'
    context_object_name = 'assignment'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = StudentProfile.objects.get(user=self.request.user)
        context['submissions'] = Submission.objects.filter(assignment=self.object, student=profile).order_by('-submitted_at')
        return context

def student_logout(request):
    logout(request)
    messages.success(request, "Successfully logged out.")
    return redirect('student_portal:student_login')