from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from core.models import Course, Department

class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200, default='Instructor Name')
    email = models.EmailField(default='instructor@example.com')
    phone = models.CharField(max_length=20, default='0000000000')
    profile_pic = CloudinaryField('profile_pic', blank=True, null=True)
    courses_taught = models.ManyToManyField(Course, related_name='instructors', blank=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True, related_name='instructors')

    def __str__(self):
        return self.full_name