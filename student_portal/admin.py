from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(StudentProfile)
admin.site.register(Semester)
admin.site.register(LearningMaterial)
admin.site.register(Assignment)
admin.site.register(Announcement)
admin.site.register(NotificationPreference)
admin.site.register(Enrollment)
admin.site.register(Submission)
