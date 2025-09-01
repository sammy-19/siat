from django.db import models
from django.contrib.auth.models import User
from cloudinary.models import CloudinaryField
from core.models import Course, EnrollmentApplication

class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    profile_pic = CloudinaryField('profile_pic', blank=True)
    courses_taught = models.ManyToManyField(Course, related_name='instructors')

    def __str__(self):
        return self.full_name