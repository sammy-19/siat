from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MaxValueValidator, MinValueValidator
from cloudinary.models import CloudinaryField
from core.models import Course, School
import datetime


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200, default='Student Name')
    email = models.EmailField(default='student@example.com')
    phone = models.CharField(max_length=20, default='0000000000')
    profile_pic = CloudinaryField('profile_pic', blank=True, null=True)
    student_number = models.CharField(max_length=50, blank=True, unique=True)
    school = models.ForeignKey(School, on_delete=models.SET_NULL, null=True, blank=True, related_name='students')

    def save(self, *args, **kwargs):
        if not self.student_number:
            last_num = StudentProfile.objects.aggregate(max_num=models.Max('id'))['max_num'] or 0
            self.student_number = f"SIAT-{datetime.datetime.now().year}-{last_num + 1:04d}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.full_name


class Enrollment(models.Model):
    """Course-level enrollment - tracks which courses a student is enrolled in"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('student', 'course')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.course.title}"


class SubjectEnrollment(models.Model):
    """Subject-level enrollment - tracks student progress, grades per subject"""
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='subject_enrollments')
    course_subject = models.ForeignKey('CourseSubject', on_delete=models.CASCADE, related_name='enrollments')
    progress = models.IntegerField(default=0, validators=[MinValueValidator(0), MaxValueValidator(100)])  # 0-100%
    grade = models.CharField(max_length=2, blank=True)  # e.g., 'A', 'B'
    final_score = models.PositiveIntegerField(null=True, blank=True, validators=[MaxValueValidator(100)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ('student', 'course_subject')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.course_subject.subject.title}"


class Semester(models.Model):
    name = models.CharField(max_length=50, default='Semester')  # e.g., 'Fall 2025'
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# Subject Model
class Subject(models.Model):
    title = models.CharField(max_length=200, default='Untitled Subject')
    code = models.CharField(max_length=20, unique=True, default='SUBJ000')
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="subjects_created")
    courses = models.ManyToManyField(Course, through='CourseSubject', related_name='subjects', blank=True)

    def __str__(self):
        return f"{self.code} - {self.title}"


# Subjects to Courses per Semester
class CourseSubject(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)
    instructor = models.ForeignKey('instructor_portal.InstructorProfile', on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('course', 'subject', 'semester')  # Prevent duplicate entries

    def __str__(self):
        return f"{self.course.title} - {self.subject.title} ({self.semester.name})"


class Assignment(models.Model):
    """Assignments are created per subject"""
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='assignments', null=True, blank=True)
    title = models.CharField(max_length=200, default='Untitled Assignment')
    description = models.TextField(default='No description provided.')
    due_date = models.DateTimeField(null=True, blank=True)
    file = models.URLField(blank=True, null=True)
    file_public_id = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-due_date']
    
    def __str__(self):
        subject_name = self.subject.title if self.subject else "No Subject"
        return f"{subject_name} - {self.title}"


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    file = CloudinaryField('file', resource_type='raw')  # Word/PDF upload
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=2, blank=True)
    score = models.PositiveIntegerField(null=True, blank=True, validators=[MaxValueValidator(100)], help_text="Score out of 100")
    
    class Meta:
        ordering = ['-submitted_at']
    
    def __str__(self):
        return f"{self.student.full_name} - {self.assignment.title}"


class LearningMaterial(models.Model):
    """Learning materials are uploaded per subject"""
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='learning_materials', null=True, blank=True)
    title = models.CharField(max_length=200, default='Untitled Material')
    # File is optional to allow video-only materials
    file = CloudinaryField('file', resource_type='raw', blank=True, null=True)
    video_url = models.URLField(blank=True, null=True, help_text="Paste a YouTube link for videos")
    type = models.CharField(max_length=20, choices=(('outline', 'Subject Outline'), ('module', 'Module'), ('video', 'Video')), default='module')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        subject_name = self.subject.title if self.subject else "No Subject"
        return f"{subject_name} - {self.title}"

    def is_valid_youtube(self):
        if not self.video_url:
            return False
        url = self.video_url.lower()
        # Accept only YouTube watch or youtu.be links
        return (
            url.startswith('https://www.youtube.com/watch') or
            url.startswith('http://www.youtube.com/watch') or
            url.startswith('https://youtube.com/watch') or
            url.startswith('http://youtube.com/watch') or
            url.startswith('https://youtu.be/') or
            url.startswith('http://youtu.be/')
        )

    def get_display_url(self):
        if self.type == 'video' and self.video_url and self.is_valid_youtube():
            return self.get_embed_url()
        elif self.file:
            return self.file.url
        return None

    def get_embed_url(self):
        if not self.video_url:
            return None
        url = self.video_url
        if 'watch?v=' in url:
            return url.replace('watch?v=', 'embed/')
        if 'youtu.be/' in url:
            return url.replace('youtu.be/', 'www.youtube.com/embed/')
        # Fallback None for non-YouTube
        return None


class NotificationPreference(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.student.full_name} - Notifications {'Enabled' if self.enabled else 'Disabled'}"


class Announcement(models.Model):
    """Announcements are made per subject"""
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE, related_name='announcements', null=True, blank=True)
    title = models.CharField(max_length=200, default='Announcement')
    content = models.TextField(default='No content provided.')
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        subject_name = self.subject.title if self.subject else "No Subject"
        return f"{subject_name} - {self.title}"
