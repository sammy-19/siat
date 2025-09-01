from django.db import models
from cloudinary.models import CloudinaryField
from django.utils.text import slugify


# class AboutSection(models.Model):
#     title = models.CharField(max_length=255)
#     content = models.TextField()
#     order = models.IntegerField(default=0)  # For sorting

#     class Meta:
#         ordering = ['order']

#     def __str__(self):
#         return self.title

class Course(models.Model):
    CATEGORY_CHOICES = (
        ('short_certificate', 'Short Certificate Course'),
        ('diploma', 'Diploma Course'),
    )
    title = models.CharField(max_length=200, blank=True)
    description = models.TextField()
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='Diploma Course')
    duration = models.CharField(max_length=100)  # e.g., '2 weeks' or '1 year'
    fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # e.g., 200.00 for cert
    image = CloudinaryField('image', blank=True, null=True)  # Thumbnail via Cloudinary
    slug = models.SlugField(unique=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

class EnrollmentApplication(models.Model):
    GENDER_CHOICES = (
        ('male', 'Male'),
        ('female', 'Female'),
        ('other', 'Other'),
        ('prefer_not_to_say', 'Prefer not to say'),
    )
    DISABILITY_CHOICES = (
        ('none', 'None'),
        ('physical', 'Physical'),
        ('visual', 'Visual'),
        ('hearing', 'Hearing'),
        ('other', 'Other'),
    )

    # Personal Info
    full_name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='Male')
    date_of_birth = models.DateField(null=True)

    # Education
    highest_qualification = models.CharField(max_length=200, default="e.g., Grade 12 Certificate, etc")  # e.g., 'High School', 'Bachelor's'
    education_background = models.TextField(default='School Name, Grades, Final Year Attended')  # Details on schools, grades, etc.

    # Next of Kin
    next_of_kin_name = models.CharField(max_length=200, null=True, blank=True)
    next_of_kin_relationship = models.CharField(max_length=100, null=True, blank=True)  # e.g., 'Parent', 'Spouse'
    next_of_kin_contact = models.CharField(max_length=20, null=True, blank=True)

    # Identity & Disability
    identity_type = models.CharField(max_length=20, choices=(('national_id', 'National ID'), ('passport', 'Passport')), default="National ID")
    identity_number = models.CharField(max_length=50, default="010101/10/1")
    disability_status = models.CharField(max_length=20, choices=DISABILITY_CHOICES, default='none')
    disability_details = models.TextField(blank=True)  # Optional if 'other'

    # Documents (Cloudinary for storage)
    identity_document = CloudinaryField('identity_document', blank=False, resource_type='raw', default='NRC')  # PDF/Image
    secondary_results = CloudinaryField('secondary_results', blank=True, resource_type='raw', default='Results')  # Required for diplomas

    # Other
    course = models.ForeignKey(Course, on_delete=models.CASCADE)
    message = models.TextField(blank=True)
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.course.title} ({self.status})"
    
class AboutSection(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self):
        return self.title

class ContactInfo(models.Model):
    phone = models.CharField(max_length=20)
    email = models.EmailField()
    address = models.TextField(blank=True)

    def __str__(self):
        return self.phone

class ContactMessage(models.Model):
    name = models.CharField(max_length=200)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"