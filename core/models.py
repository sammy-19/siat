from django.db import models
from cloudinary.models import CloudinaryField
from django.utils.text import slugify


class School(models.Model):
    name = models.CharField(max_length=255, unique=True)
    
    def __str__(self):
        return self.name

class Department(models.Model):
    school = models.ForeignKey(School, on_delete=models.CASCADE, related_name='departments')
    name = models.CharField(max_length=255)
    class Meta:
        unique_together = ('school', 'name')
        
    def __str__(self):
        return f"{self.school.name} - {self.name}"

class Course(models.Model):
    CATEGORY_CHOICES = (
        ('short_certificate', 'Short Certificate Course'),
        ('diploma', 'Diploma Course'),
    )
    title = models.CharField(max_length=200, default='Untitled Course')
    description = models.TextField(default='No description provided.')
    category = models.CharField(max_length=20, choices=CATEGORY_CHOICES, default='diploma')
    duration = models.CharField(max_length=100, default='Not specified')  # e.g., '2 weeks' or '1 year'
    fee = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)  # e.g., 200.00 for cert
    image = CloudinaryField('image', blank=True, null=True)  # Thumbnail via Cloudinary
    slug = models.SlugField(unique=True, blank=True)

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
    full_name = models.CharField(max_length=200, default='Full Name')
    email = models.EmailField(default='email@example.com')
    phone = models.CharField(max_length=20, default='0000000000')
    gender = models.CharField(max_length=20, choices=GENDER_CHOICES, default='male')
    date_of_birth = models.DateField(null=True, blank=True)

    # Education
    highest_qualification = models.CharField(max_length=200, default="Grade 12 Certificate")
    education_background = models.TextField(default='School Name, Grades, Final Year Attended')

    # Next of Kin
    next_of_kin_name = models.CharField(max_length=200, null=True, blank=True)
    next_of_kin_relationship = models.CharField(max_length=100, null=True, blank=True)  # e.g., 'Parent', 'Spouse'
    next_of_kin_contact = models.CharField(max_length=20, null=True, blank=True)

    # Identity & Disability
    identity_type = models.CharField(max_length=20, choices=(('national_id', 'National ID'), ('passport', 'Passport')), default='national_id')
    identity_number = models.CharField(max_length=50, default="010101/10/1")
    disability_status = models.CharField(max_length=20, choices=DISABILITY_CHOICES, default='none')
    disability_details = models.TextField(blank=True)  # Optional if 'other'

    # Documents (Cloudinary for storage)
    identity_document = CloudinaryField('identity_document', resource_type='raw')  # PDF/Image
    secondary_results = CloudinaryField('secondary_results', blank=True, null=True, resource_type='raw')  # Required for diplomas

    # Other
    course = models.ForeignKey(Course, on_delete=models.CASCADE, null=True, blank=True)
    message = models.TextField(blank=True, default='')
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    applied_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.full_name} - {self.course.title} ({self.status})"

class ContactInfo(models.Model):
    phone = models.CharField(max_length=20, default='0000000000')
    email = models.EmailField(default='info@example.com')
    address = models.TextField(blank=True, default='')

    def __str__(self):
        return self.phone

class ContactMessage(models.Model):
    name = models.CharField(max_length=200, default='Anonymous')
    email = models.EmailField(default='email@example.com')
    subject = models.CharField(max_length=200, default='No Subject')
    message = models.TextField(default='No message provided.')
    sent_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} - {self.subject}"