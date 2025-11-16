from django.contrib import admin
from .models import Course, ContactInfo, EnrollmentApplication, School, Department, ContactMessage

admin.site.register(Course)
admin.site.register(ContactInfo)
admin.site.register(ContactMessage)
admin.site.register(EnrollmentApplication)
admin.site.register(School)
admin.site.register(Department)