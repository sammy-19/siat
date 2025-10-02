from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import DetailView
from .models import Enrollment, Assignment, Submission, LearningMaterial, Semester, StudentProfile, NotificationPreference, Announcement
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

    # Attach avg_score to each enrollment
    course_labels = []
    avg_scores = []
    for enrollment in enrollments:
        avg_score = (
            Submission.objects.filter(
                assignment__course=enrollment.course,
                student=profile
            ).aggregate(avg=models.Avg("score"))["avg"]
        )
        enrollment.avg_score = round(avg_score, 2) if avg_score is not None else None

        course_labels.append(enrollment.course.title)
        avg_scores.append(enrollment.avg_score or 0)

    overall_progress = enrollments.aggregate(avg_progress=models.Avg('progress'))['avg_progress'] or 0
    notification_pref = NotificationPreference.objects.get_or_create(student=profile)[0]
    if request.GET.get('toggle_notifications'):
        notification_pref.enabled = not notification_pref.enabled
        notification_pref.save()
        return redirect('student_portal:dashboard')

    announcements = Announcement.objects.filter(course__in=[e.course for e in enrollments]).order_by('-created_at')[:5]

    # Overall average score
    overall_avg_score = sum(avg_scores) / len(avg_scores) if avg_scores else 0

    context = {
        'profile': profile,
        'enrollments': enrollments,
        'overall_progress': overall_progress,
        'avg_score': overall_avg_score,
        'course_labels': course_labels,
        'avg_scores': avg_scores,
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
    assignments = Assignment.objects.filter(course__in=[e.course for e in enrollments])
    if request.method == 'POST':
        form = SubmissionForm(request.POST, request.FILES)
        if form.is_valid():
            submission = form.save(commit=False)
            submission.assignment = get_object_or_404(Assignment, id=request.POST['assignment_id'])
            submission.student = profile
            submission.save()
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
    if not enrollments.exists():
        logger.warning(f"No enrollments found for student {profile.user.username}")
        materials = LearningMaterial.objects.none()  # Empty queryset
    else:
        course_ids = [e.course.id for e in enrollments]
        materials = LearningMaterial.objects.filter(course_id__in=course_ids).order_by('-created_at')
        if not materials.exists():
            logger.warning(f"No materials found for courses {course_ids} for student {profile.user.username}")

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
        materials = LearningMaterial.objects.filter(course=self.object).order_by('-created_at')
        
        materials_by_type = {
        'outline': materials.filter(type='outline'),
        'module': materials.filter(type='module'),
        'video': materials.filter(type='video'),
    }
        context['enrollment'] = Enrollment.objects.get(student=profile, course=self.object)
        context['assignments'] = Assignment.objects.filter(course=self.object).order_by('-created_at')
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