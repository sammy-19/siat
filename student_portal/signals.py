from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Submission, SubjectEnrollment, Assignment, LearningMaterial, CourseSubject, Semester


def calculate_subject_progress(student, subject):
    """
    Calculate progress for a student in a specific subject.
    Progress is based on:
    - 70% Assignment completion (submitted vs total)
    - 30% Average assignment score
    """
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        return 0
    
    # Get total assignments for this subject
    total_assignments = Assignment.objects.filter(subject=subject).count()
    
    if total_assignments == 0:
        # If no assignments, progress is 100% (subject has no requirements)
        return 100
    
    # Get submitted assignments
    submitted_assignments = Submission.objects.filter(
        student=student,
        assignment__subject=subject
    ).count()
    
    # Calculate completion percentage (70% weight)
    completion_rate = (submitted_assignments / total_assignments) * 70
    
    # Calculate average score (30% weight)
    from django.db.models import Avg
    avg_score = Submission.objects.filter(
        student=student,
        assignment__subject=subject,
        score__isnull=False
    ).aggregate(avg=Avg('score'))['avg']
    
    score_contribution = (avg_score * 0.3) if avg_score else 0
    
    # Total progress
    total_progress = completion_rate + score_contribution
    
    return min(int(total_progress), 100)  # Cap at 100%


def update_all_subject_enrollments(student):
    """
    Update progress for all of a student's subject enrollments
    """
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        return
    
    # Get all course subjects for current semester
    from .models import Enrollment
    student_courses = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
    
    course_subjects = CourseSubject.objects.filter(
        course_id__in=student_courses,
        semester=current_semester,
        is_active=True
    )
    
    for course_subject in course_subjects:
        # Get or create SubjectEnrollment
        subject_enrollment, created = SubjectEnrollment.objects.get_or_create(
            student=student,
            course_subject=course_subject
        )
        
        # Calculate and update progress
        new_progress = calculate_subject_progress(student, course_subject.subject)
        subject_enrollment.progress = new_progress
        subject_enrollment.save()


@receiver(post_save, sender=Submission)
def update_progress_on_submission(sender, instance, created, **kwargs):
    """
    Automatically update progress when a student submits an assignment
    """
    if created:
        # New submission - update progress for this subject
        student = instance.student
        subject = instance.assignment.subject
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            return
        
        # Get the course_subject for this assignment
        from .models import Enrollment
        student_courses = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
        
        course_subject = CourseSubject.objects.filter(
            subject=subject,
            course_id__in=student_courses,
            semester=current_semester
        ).first()
        
        if course_subject:
            # Get or create SubjectEnrollment
            subject_enrollment, enrollment_created = SubjectEnrollment.objects.get_or_create(
                student=student,
                course_subject=course_subject
            )
            
            # Calculate new progress
            new_progress = calculate_subject_progress(student, subject)
            subject_enrollment.progress = new_progress
            subject_enrollment.save()
            
            print(f"✅ Updated progress for {student.full_name} in {subject.title}: {new_progress}%")
    
    # Also update when score is added/changed
    elif instance.score is not None:
        student = instance.student
        subject = instance.assignment.subject
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            return
        
        from .models import Enrollment
        student_courses = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
        
        course_subject = CourseSubject.objects.filter(
            subject=subject,
            course_id__in=student_courses,
            semester=current_semester
        ).first()
        
        if course_subject:
            subject_enrollment = SubjectEnrollment.objects.filter(
                student=student,
                course_subject=course_subject
            ).first()
            
            if subject_enrollment:
                new_progress = calculate_subject_progress(student, subject)
                subject_enrollment.progress = new_progress
                subject_enrollment.save()
                
                print(f"✅ Updated progress for {student.full_name} in {subject.title}: {new_progress}% (score updated)")
