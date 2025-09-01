from django.db import models
from core.models import Course  # For course assignments

class AboutSection(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title

class PortalSettings(models.Model):
    student_portal_active = models.BooleanField(default=True)
    instructor_portal_active = models.BooleanField(default=True)
    maintenance_message = models.TextField(blank=True)

    def __str__(self):
        return "Portal Settings"