from django.core.management.base import BaseCommand
from student_portal.models import StudentProfile, Semester, CourseSubject, SubjectEnrollment, Enrollment
from student_portal.signals import calculate_subject_progress


class Command(BaseCommand):
    help = 'Sync progress for all students based on their current submissions'

    def add_arguments(self, parser):
        parser.add_argument(
            '--student-id',
            type=int,
            help='Update progress for a specific student by ID',
        )

    def handle(self, *args, **options):
        student_id = options.get('student_id')
        
        current_semester = Semester.objects.filter(is_current=True).first()
        
        if not current_semester:
            self.stdout.write(self.style.ERROR('No current semester found!'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Current Semester: {current_semester.name}'))
        
        # Get students to process
        if student_id:
            students = StudentProfile.objects.filter(id=student_id)
            if not students.exists():
                self.stdout.write(self.style.ERROR(f'Student with ID {student_id} not found!'))
                return
        else:
            students = StudentProfile.objects.all()
        
        total_updated = 0
        total_created = 0
        
        for student in students:
            self.stdout.write(f'\nProcessing: {student.full_name} ({student.student_number})')
            
            # Get student's enrolled courses
            student_courses = Enrollment.objects.filter(student=student).values_list('course_id', flat=True)
            
            if not student_courses:
                self.stdout.write(self.style.WARNING(f'  ⚠ No course enrollments found'))
                continue
            
            # Get all course subjects for current semester
            course_subjects = CourseSubject.objects.filter(
                course_id__in=student_courses,
                semester=current_semester,
                is_active=True
            ).select_related('subject', 'course')
            
            if not course_subjects:
                self.stdout.write(self.style.WARNING(f'  ⚠ No active subjects in current semester'))
                continue
            
            for course_subject in course_subjects:
                # Get or create SubjectEnrollment
                subject_enrollment, created = SubjectEnrollment.objects.get_or_create(
                    student=student,
                    course_subject=course_subject
                )
                
                # Calculate progress
                old_progress = subject_enrollment.progress
                new_progress = calculate_subject_progress(student, course_subject.subject)
                
                subject_enrollment.progress = new_progress
                subject_enrollment.save()
                
                if created:
                    total_created += 1
                    self.stdout.write(self.style.SUCCESS(
                        f'  ✅ Created: {course_subject.subject.code} - Progress: {new_progress}%'
                    ))
                else:
                    total_updated += 1
                    if old_progress != new_progress:
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✅ Updated: {course_subject.subject.code} - {old_progress}% → {new_progress}%'
                        ))
                    else:
                        self.stdout.write(
                            f'  ➖ No change: {course_subject.subject.code} - {new_progress}%'
                        )
        
        self.stdout.write(self.style.SUCCESS(f'\n{"="*60}'))
        self.stdout.write(self.style.SUCCESS(f'Sync Complete!'))
        self.stdout.write(self.style.SUCCESS(f'Created: {total_created} subject enrollments'))
        self.stdout.write(self.style.SUCCESS(f'Updated: {total_updated} subject enrollments'))
        self.stdout.write(self.style.SUCCESS(f'{"="*60}'))
