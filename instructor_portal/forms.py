from django import forms
from django.contrib.auth.models import User
from core.models import EnrollmentApplication
from student_portal.models import Enrollment

class StudentRegistrationForm(forms.Form):
    enrollment = forms.ModelChoiceField(queryset=EnrollmentApplication.objects.all())
    student_number = forms.CharField(max_length=50, required=True)

    def save(self):
        enrollment = self.cleaned_data['enrollment']
        student = Enrollment.student  # Assuming Enrollment has student FK to StudentProfile
        if not student.user:
            username = student.email.split('@')[0]
            password = User.objects.make_random_password()
            user = User.objects.create_user(username=username, email=student.email, password=password)
            student.user = user
            student.student_number = self.cleaned_data['student_number']
            student.save()
            # Send email with password
            from django.core.mail import send_mail
            send_mail(
                'Your Student Account is Ready',
                f"Dear {student.full_name},\nYour student number: {student.student_number}\nUsername: {username}\nPassword: {password}\nLog in at /portal/login/",
                'sunriseinstituteofapplied21@gmail.com',
                [student.email]
            )
        return student