from django.contrib import admin
from .models import InstructorProfile

# Register your models here.
@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone')