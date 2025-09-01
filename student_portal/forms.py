from django import forms
from .models import Submission, StudentProfile

class SubmissionForm(forms.ModelForm):
    class Meta:
        model = Submission
        fields = ['file']
        widgets = {'file': forms.FileInput(attrs={'accept': '.pdf,.doc,.docx'})}

class ProfileForm(forms.ModelForm):
    class Meta:
        model = StudentProfile
        fields = ['full_name', 'email', 'phone', 'profile_pic']