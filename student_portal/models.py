from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from core.models import Course, School
from instructor_portal.models import InstructorProfile
import datetime


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    profile_pic = CloudinaryField('profile_pic', blank=True)
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
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    progress = models.IntegerField(default=0)  # 0-100%
    grade = models.CharField(max_length=2, blank=True)  # e.g., 'A', 'B'
    created_at = models.DateTimeField(auto_now_add=True)


class Semester(models.Model):
    name = models.CharField(max_length=50)  # e.g., 'Fall 2025'
    start_date = models.DateField()
    end_date = models.DateField()
    is_current = models.BooleanField(default=False)

    def __str__(self):
        return self.name


# Subject Model
class Subject(models.Model):
    title = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=False, default="Code")
    description = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name="subjects_created")
    courses = models.ManyToManyField(Course, through='CourseSubject', related_name='subjects')

    def __str__(self):
        return f"{self.code} - {self.title}"


# Subjects to Courses per Semester
class CourseSubject(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    subject = models.ForeignKey('Subject', on_delete=models.CASCADE)
    semester = models.ForeignKey('Semester', on_delete=models.CASCADE)
    instructor = models.ForeignKey(InstructorProfile, on_delete=models.SET_NULL, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('course', 'subject', 'semester')  # Prevent duplicate entries

    def __str__(self):
        return f"{self.course.title} - {self.subject.title} ({self.semester.name})"


class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    file = models.URLField(blank=True, null=True)
    file_public_id = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    file = CloudinaryField('file', resource_type='raw')  # Word/PDF upload
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=2, blank=True)
    score = models.PositiveIntegerField(null=True, blank=True, help_text="Score out of 100")


class LearningMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = CloudinaryField('file', resource_type='raw')
    video_url = models.URLField(blank=True, null=True, help_text="Paste a YouTube link for videos")
    type = models.CharField(max_length=20, choices=(('outline', 'Course Outline'), ('module', 'Module'), ('video', 'Video')))
    created_at = models.DateTimeField(auto_now_add=True)

    def get_display_url(self):
        if self.type == 'video' and self.video_url:
            return self.get_embed_url()
        elif self.file:
            return self.file.url
        return None

    def get_embed_url(self):
        if not self.video_url:
            return None
        if "watch?v=" in self.video_url:
            return self.video_url.replace("watch?v=", "embed/")
        return self.video_url


class NotificationPreference(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)


class Announcement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
