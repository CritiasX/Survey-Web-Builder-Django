from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.

class Section(models.Model):
    name = models.CharField(max_length=150)
    teacher = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sections')

    def __str__(self):
        return f"{self.name} ({self.teacher.username})"

class User(AbstractUser):
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('teacher', 'Teacher'),
    ]

    role = models.CharField('role', max_length=20, choices=ROLE_CHOICES, default='student')
    # optional section association for students
    section = models.ForeignKey(Section, null=True, blank=True, on_delete=models.SET_NULL, related_name='students')

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
