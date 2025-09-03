from django import forms
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings
from core.models import Course, EnrollmentApplication, School, Department
from student_portal.models import StudentProfile, Enrollment
from instructor_portal.models import InstructorProfile
from .models import *
from datetime import datetime


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

class InstructorRegistrationForm(forms.ModelForm):
    courses = forms.ModelMultipleChoiceField(queryset=Course.objects.all(), widget=forms.CheckboxSelectMultiple, required=False)

    class Meta:
        model = InstructorProfile
        fields = ('full_name', 'email', 'phone', 'profile_pic')

    def save(self, commit=True):
        profile = super().save(commit=False)
        username = profile.email.split('@')[0]
        password = "securepass123"
        user = User.objects.create_user(username=username, email=profile.email, password=password)
        profile.user = user
        if commit:
            profile.save()
            self.save_m2m()
        send_mail(
            'Your SIAT Instructor Account is Ready',
            f"Dear {profile.full_name},\nUsername: {username}\nInitial Password: {password} (change on first login)\nLog in at /instructor/login/",
            settings.DEFAULT_FROM_EMAIL,
            [profile.email]
        )
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