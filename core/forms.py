from django import forms
from .models import EnrollmentApplication, Course, ContactMessage

class EnrollmentForm(forms.ModelForm):
    class Meta:
        model = EnrollmentApplication
        fields = [
            'full_name', 'email', 'phone', 'gender', 'date_of_birth',
            'highest_qualification', 'education_background',
            'next_of_kin_name', 'next_of_kin_relationship', 'next_of_kin_contact',
            'identity_type', 'identity_number', 'disability_status', 'disability_details',
            'identity_document', 'secondary_results',
            'course', 'message'
        ]
        widgets = {
            'date_of_birth': forms.DateInput(attrs={'type': 'date'}),
            'gender': forms.Select(),
            'disability_status': forms.Select(),
            'identity_type': forms.Select(),
            'education_background': forms.Textarea(attrs={'rows': 4}),
            'disability_details': forms.Textarea(attrs={'rows': 3}),
            'message': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.all()
        self.fields['secondary_results'].required = False  # Dynamic in clean

    def clean(self):
        cleaned_data = super().clean()
        course = cleaned_data.get('course')
        if course and course.category == 'diploma' and not cleaned_data.get('secondary_results'):
            self.add_error('secondary_results', 'Secondary results are required for Diploma courses.')
        return cleaned_data

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['course'].queryset = Course.objects.all()  # Dropdown of all courses
        
class ContactForm(forms.ModelForm):
    class Meta:
        model = ContactMessage
        fields = ['name', 'email', 'subject', 'message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 5}),
        }