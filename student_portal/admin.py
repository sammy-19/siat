from django.contrib import admin
from .models import *

# Register your models here.
admin.site.register(StudentProfile)
admin.site.register(LearningMaterial)
admin.site.register(Assignment)
admin.site.register(Announcement)
admin.site.register(NotificationPreference)
admin.site.register(Enrollment)
admin.site.register(Submission)

class CourseSubjectInline(admin.TabularInline):
    model = CourseSubject
    extra = 1


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ('code', 'title', 'created_by')
    search_fields = ('title', 'code')
    inlines = [CourseSubjectInline]


@admin.register(CourseSubject)
class CourseSubjectAdmin(admin.ModelAdmin):
    list_display = ('course', 'subject', 'semester', 'instructor', 'is_active')
    list_filter = ('semester', 'course', 'instructor', 'is_active')


@admin.register(Semester)
class SemesterAdmin(admin.ModelAdmin):
    list_display = ('name', 'start_date', 'end_date', 'is_current')
    list_filter = ('is_current',)

