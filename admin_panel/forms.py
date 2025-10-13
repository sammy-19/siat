from django import forms
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from core.models import Course, EnrollmentApplication, School, Department
from student_portal.models import StudentProfile, Enrollment, Subject
from instructor_portal.models import InstructorProfile
from .models import *
from datetime import datetime


class SubjectForm(forms.ModelForm):
    class Meta:
        model = Subject
        fields = ['title', 'code', 'description']
        widgets = {
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subject name'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter subject code'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter brief description'}),
        }


class SchoolForm(forms.ModelForm):
    class Meta:
        model = School
        fields = ['name']

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['school', 'name']

class StudentSchoolForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['school']

class InstructorDepartmentForm(forms.ModelForm):
    class Meta:
        model = InstructorProfile
        fields = ['department']


class StudentRegistrationForm(forms.Form):
    application = forms.ModelChoiceField(queryset=EnrollmentApplication.objects.filter(status='pending'))
    # Additional fields if needed

    def save(self):
        app = self.cleaned_data['application']
        last_id = StudentProfile.objects.aggregate(max_id=models.Max('id'))['max_id'] or 0
        student_number = f"SIAT-{datetime.now().year}-{last_id + 1:04d}"
        username = app.email.split('@')[0]
        user = User.objects.create_user(username=username, email=app.email, password=student_number)  # Password = student_number
        profile = StudentProfile.objects.create(
            user=user,
            full_name=app.full_name,
            email=app.email,
            phone=app.phone,
            student_number=student_number
        )
        if app.identity_document:
            profile.profile_pic = app.identity_document
        profile.save()
        Enrollment.objects.create(student=profile, course=app.course)
        app.status = 'accepted'
        app.save()
        send_mail(
            'Your SIAT Student Account is Ready',
            f"Dear {app.full_name},\nUsername: {username}\nInitial Password: {student_number} (your student number - change on first login)\nLog in at /portal/login/",
            settings.DEFAULT_FROM_EMAIL,
            [app.email]
        )
        return profile
    
class StudentEditForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['full_name', 'email', 'phone', 'profile_pic', 'school']

class InstructorRegistrationForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Courses Taught"
    )

    class Meta:
        model = InstructorProfile
        fields = ('full_name', 'email', 'phone', 'profile_pic', 'department')

    def save(self, commit=True):
        profile = super().save(commit=False)
        username = profile.email.split('@')[0]
        password = "securepass123"

        # Create linked user
        user = User.objects.create_user(username=username, email=profile.email, password=password)
        profile.user = user

        if commit:
            profile.save()
            # Assign selected courses
            selected_courses = self.cleaned_data.get('courses')
            if selected_courses:
                profile.courses_taught.set(selected_courses)
            self.save_m2m()

        # Send login info via email
        send_mail(
            'Your SIAT Instructor Account is Ready',
            f"Dear {profile.full_name},\n\n"
            f"Username: {username}\n"
            f"Initial Password: {password} (please change it after first login)\n"
            f"Log in at /instructor/login/\n\n"
            "Best regards,\nSIAT Admin",
            settings.DEFAULT_FROM_EMAIL,
            [profile.email]
        )
        return profile

class InstructorEditForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(
        queryset=Course.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Courses Taught"
    )

    class Meta:
        model = InstructorProfile
        fields = ('full_name', 'email', 'phone', 'profile_pic', 'department', 'courses')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-select current courses if editing an existing instructor
        if self.instance and self.instance.pk:
            self.fields['courses'].initial = self.instance.courses_taught.all()

    def save(self, commit=True):
        profile = super().save(commit=False)

        # Update linked user details
        user = profile.user
        user.email = profile.email
        user.first_name = profile.full_name.split(" ")[0]
        user.last_name = " ".join(profile.full_name.split(" ")[1:])
        user.save()

        if commit:
            profile.save()

            # Update selected courses
            selected_courses = self.cleaned_data.get('courses')
            if selected_courses is not None:
                profile.courses_taught.set(selected_courses)
            self.save_m2m()

        return profile


class AboutSectionForm(forms.ModelForm):
    class Meta:
        model = AboutSection
        fields = ('title', 'content', 'order')
        widgets = {
            'content': forms.Textarea(attrs={'rows': 10}),
        }

class PortalSettingsForm(forms.ModelForm):
    class Meta:
        model = PortalSettings
        fields = ('student_portal_active', 'instructor_portal_active', 'maintenance_message')
        widgets = {
            'maintenance_message': forms.Textarea(attrs={'rows': 4}),
        }