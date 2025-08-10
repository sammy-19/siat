from django.contrib import admin
from django.contrib import admin
from .models import Course, AboutSection, ContactInfo, EnrollmentApplication

admin.site.register(Course)
admin.site.register(AboutSection)
admin.site.register(ContactInfo)
admin.site.register(EnrollmentApplication)