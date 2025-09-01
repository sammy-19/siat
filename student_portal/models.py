from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from core.models import Course
import datetime


class StudentProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    profile_pic = CloudinaryField('profile_pic', blank=True)  # Upload via Cloudinary
    student_number = models.CharField(max_length=50, blank=True, unique=True)

    def save(self, *args, **kwargs):
        if not self.student_number:
            last_num = StudentProfile.objects.aggregate(max_num=models.Max('id'))['max_num'] or 0
            self.student_number = f"SIAT-{datetime.now().year}-{last_num + 1:04d}"
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

class Assignment(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    description = models.TextField()
    due_date = models.DateTimeField()
    # file = CloudinaryField('file', blank=True, resource_type='raw')
    file = models.URLField(blank=True, null=True)
    file_public_id = models.CharField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True) # Optional assignment file

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    file = CloudinaryField('file', resource_type='raw')  # Word/PDF upload
    submitted_at = models.DateTimeField(auto_now_add=True)
    grade = models.CharField(max_length=2, blank=True)

class LearningMaterial(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    file = CloudinaryField('file', resource_type='raw')  # PDF/module/video
    type = models.CharField(max_length=20, choices=(('outline', 'Course Outline'), ('module', 'Module'), ('video', 'Video')))
    created_at = models.DateTimeField(auto_now_add=True)
    
    def get_file_url(self):
        # Optional: Add Cloudinary transformation for PDF preview if needed
        if self.type == 'video':
            return self.file.url
        return f"{self.file.url}?download=1"

class NotificationPreference(models.Model):
    student = models.OneToOneField(StudentProfile, on_delete=models.CASCADE)
    enabled = models.BooleanField(default=False)

class Announcement(models.Model):
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    title = models.CharField(max_length=200)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
