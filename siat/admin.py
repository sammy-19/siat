from django.contrib import admin
from django.contrib.auth.models import User, Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail
from django.conf import settings
from student_portal.models import StudentProfile, Enrollment
from instructor_portal.models import InstructorProfile
from core.models import Course, AboutSection, EnrollmentApplication

class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'email', 'is_staff', 'groups_list')
    def groups_list(self, obj):
        return ", ".join([g.name for g in obj.groups.all()])
    groups_list.short_description = 'Groups'

admin.site.unregister(User)
admin.site.register(User, UserAdmin)

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'student_number', 'courses_enrolled')
    actions = ['register_students']
    def courses_enrolled(self, obj):
        return ", ".join([e.course.title for e in obj.enrollment_set.all()])
    def register_students(self, request, queryset):
        for profile in queryset:
            if not profile.user:
                username = profile.email.split('@')[0]
                password = profile.student_number  # Use student_number as initial password
                user = User.objects.create_user(username=username, email=profile.email, password=password)
                profile.user = user
                user.groups.add(Group.objects.get(name='Student'))
                profile.save()
                send_mail(
                    'Your SIAT Student Account is Ready',
                    f"Dear {profile.full_name},\nUsername: {username}\nInitial Password: {password} (change on first login)\nLog in at /portal/login/",
                    settings.DEFAULT_FROM_EMAIL,
                    [profile.email]
                )
        self.message_user(request, f"{queryset.count()} students registered and emailed.")
    register_students.short_description = "Register selected students (generate user/password)"

@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'courses_taught_list')
    filter_horizontal = ('courses_taught',)  # Form for assigning multiple courses
    actions = ['register_instructors']
    def courses_taught_list(self, obj):
        return ", ".join([c.title for c in obj.courses_taught.all()])
    def register_instructors(self, request, queryset):
        for profile in queryset:
            if not profile.user:
                username = profile.email.split('@')[0]
                password = User.objects.make_random_password()
                user = User.objects.create_user(username=username, email=profile.email, password=password)
                profile.user = user
                user.groups.add(Group.objects.get(name='Instructor'))
                profile.save()
                send_mail(
                    'Your SIAT Instructor Account is Ready',
                    f"Dear {profile.full_name},\nUsername: {username}\nInitial Password: {password} (change on first login)\nLog in at /instructor/login/",
                    settings.DEFAULT_FROM_EMAIL,
                    [profile.email]
                )
        self.message_user(request, f"{queryset.count()} instructors registered and emailed.")
    register_instructors.short_description = "Register selected instructors (generate user/password)"

@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    ordering = ['order']

# Custom AdminSite for CMS control
class SIATAdminSite(admin.AdminSite):
    site_header = "SIAT Administration Panel"
    site_title = "SIAT Admin"
    index_title = "Manage Students, Instructors, Courses, and Portals"
    index_template = 'admin/custom_index.html'  # Custom dashboard with links to portals

admin.site = SIATAdminSite()