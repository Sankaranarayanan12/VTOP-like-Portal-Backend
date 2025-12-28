from django.contrib.auth.models import AbstractUser
from django.db import models

from django.conf import settings
class User(AbstractUser):
    ROLE_CHOICES = (
        ('Admin', 'Admin'),
        ('Student', 'Student'),
        ('Faculty', 'Faculty'),
        ('Parent', 'Parent'),
    )
    role = models.CharField(max_length=10, choices=ROLE_CHOICES)
    linked_student = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        limit_choices_to={'role': 'Student'}
    )

    def __str__(self):
        return f"{self.username} ({self.role})"
    



class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    credits = models.PositiveIntegerField()

    slot = models.CharField(
        max_length=5,
        choices=(
            ('A', 'A'),
            ('B', 'B'),
            ('C1', 'C1'),
            ('C2', 'C2'),
        )
    )

    faculty = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'Faculty'},
        related_name='subjects'
    )

    def __str__(self):
        return f"{self.code} - {self.name}"

class Enrollment(models.Model):
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        limit_choices_to={'role': 'Student'},
        related_name='enrollments'
    )

    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='enrollments'
    )

    marks = models.FloatField(null=True, blank=True)
    attendance = models.PositiveIntegerField(default=0)
    grade = models.CharField(max_length=2, null=True, blank=True)

    revaluation_requested = models.BooleanField(default=False)
    revaluation_approved = models.BooleanField(default=False)
    revaluation_deadline = models.DateTimeField(null=True, blank=True)
    class Meta:
        unique_together = ('student', 'subject')

    def __str__(self):
        return f"{self.student.username} - {self.subject.code}"
class CourseContent(models.Model):
    subject = models.ForeignKey(
        Subject,
        on_delete=models.CASCADE,
        related_name='contents'
    )
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    content_link = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.subject.code} - {self.title}"

