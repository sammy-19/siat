"""
Utility functions for student portal
"""
from .models import SubjectEnrollment, CourseSubject, Semester, Enrollment
from .signals import calculate_subject_progress


def update_student_progress(student, subject):
    """
    Manually trigger progress update for a student in a specific subject
    
    Args:
        student: StudentProfile instance
        subject: Subject instance
    
    Returns:
        Updated progress value (0-100)
    """
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        return 0
    
    # Get student's courses
    student_courses = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
    
    # Find the course_subject
    course_subject = CourseSubject.objects.filter(
        subject=subject,
        course_id__in=student_courses,
        semester=current_semester
    ).first()
    
    if not course_subject:
        return 0
    
    # Get or create SubjectEnrollment
    subject_enrollment, created = SubjectEnrollment.objects.get_or_create(
        student=student,
        course_subject=course_subject
    )
    
    # Calculate and save new progress
    new_progress = calculate_subject_progress(student, subject)
    subject_enrollment.progress = new_progress
    subject_enrollment.save()
    
    return new_progress


def bulk_update_all_students_progress():
    """
    Update progress for ALL students in the system
    Useful for batch updates or migrations
    
    Returns:
        Dictionary with update statistics
    """
    from .models import StudentProfile
    
    current_semester = Semester.objects.filter(is_current=True).first()
    if not current_semester:
        return {'error': 'No current semester found'}
    
    stats = {
        'total_students': 0,
        'enrollments_created': 0,
        'enrollments_updated': 0,
        'errors': 0
    }
    
    students = StudentProfile.objects.all()
    stats['total_students'] = students.count()
    
    for student in students:
        try:
            student_courses = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
            
            course_subjects = CourseSubject.objects.filter(
                course_id__in=student_courses,
                semester=current_semester,
                is_active=True
            )
            
            for course_subject in course_subjects:
                subject_enrollment, created = SubjectEnrollment.objects.get_or_create(
                    student=student,
                    course_subject=course_subject
                )
                
                new_progress = calculate_subject_progress(student, course_subject.subject)
                subject_enrollment.progress = new_progress
                subject_enrollment.save()
                
                if created:
                    stats['enrollments_created'] += 1
                else:
                    stats['enrollments_updated'] += 1
                    
        except Exception as e:
            stats['errors'] += 1
            print(f"Error updating progress for {student.full_name}: {str(e)}")
    
    return stats
