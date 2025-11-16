from django import forms
from django.contrib.auth.models import User
from core.models import EnrollmentApplication
from student_portal.models import Enrollment, CourseSubject, Subject, Semester
from core.models import Course


class StudentRegistrationForm(forms.Form):
    enrollment_application = forms.ModelChoiceField(queryset=EnrollmentApplication.objects.filter(status='accepted'))
    student_number = forms.CharField(max_length=50, required=True)

    def save(self):
        from student_portal.models import StudentProfile
        enrollment_app = self.cleaned_data['enrollment_application']
        
        # Create StudentProfile from accepted enrollment application
        student, created = StudentProfile.objects.get_or_create(
            email=enrollment_app.email,
            defaults={
                'full_name': enrollment_app.full_name,
                'phone': enrollment_app.phone,
                'student_number': self.cleaned_data['student_number']
            }
        )
        
        if created and not student.user:
            username = student.email.split('@')[0]
            password = User.objects.make_random_password()
            user = User.objects.create_user(username=username, email=student.email, password=password)
            student.user = user
            student.save()
            
            # Send email with password
            from django.core.mail import send_mail
            from django.conf import settings
            send_mail(
                'Your Student Account is Ready',
                f"Dear {student.full_name},\nYour student number: {student.student_number}\nUsername: {username}\nPassword: {password}\nLog in at /portal/login/",
                settings.DEFAULT_FROM_EMAIL,
                [student.email]
            )
        return student

class CourseSubjectForm(forms.ModelForm):
    class Meta:
        model = CourseSubject
        fields = ['course', 'subject', 'semester']

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super(CourseSubjectForm, self).__init__(*args, **kwargs)

        # Only show current semester
        self.fields['semester'].queryset = Semester.objects.filter(is_current=True)

        # If instructor, restrict to their assigned courses
        if user and not user.is_superuser:
            try:
                from instructor_portal.models import InstructorProfile
                instructor_profile = InstructorProfile.objects.get(user=user)
                self.fields['course'].queryset = instructor_profile.courses_taught.all()
            except InstructorProfile.DoesNotExist:
                self.fields['course'].queryset = Course.objects.none()
        # Subjects list comes from admin-created pool
        self.fields['subject'].queryset = Subject.objects.all()
