from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        STUDENT = 'student', 'IT Student (Borrower)'
        CUSTODIAN = 'custodian', 'Laboratory Custodian (Staff)'

    YEAR_LEVEL_CHOICES = [
        ('1st Year', '1st Year'),
        ('2nd Year', '2nd Year'),
        ('3rd Year', '3rd Year'),
        ('4th Year', '4th Year'),
        ('Faculty/Staff', 'Faculty / Staff'),
    ]

    # Required email field made unique
    email = models.EmailField(unique=True, verbose_name='Email Address')
    
    # Custom project-specific fields
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        help_text='User role in BorrowTech laboratory management system.'
    )
    student_id = models.CharField(
        max_length=30,
        blank=True,
        null=True,
        verbose_name='Student / Staff ID Number',
        help_text='University institutional ID (e.g., 2024-IT-0142)'
    )
    contact_number = models.CharField(
        max_length=25,
        blank=True,
        null=True,
        verbose_name='Contact Number',
        help_text='Active phone number for borrowing notifications & due reminders'
    )
    department = models.CharField(
        max_length=120,
        default='College of Computer Studies (IT Dept)',
        verbose_name='Department / Laboratory Unit'
    )
    year_level = models.CharField(
        max_length=20,
        choices=YEAR_LEVEL_CHOICES,
        default='1st Year',
        blank=True,
        verbose_name='Year Level / Status'
    )
    profile_photo = models.ImageField(
        upload_to='profile_photos/',
        blank=True,
        null=True,
        verbose_name='Profile Photo'
    )

    def is_student_user(self):
        return self.role == self.Role.STUDENT

    def is_custodian_user(self):
        return self.role == self.Role.CUSTODIAN

    def get_dashboard_url(self):
        if self.role == self.Role.CUSTODIAN:
            return '/dashboard/custodian/'
        return '/dashboard/student/'

    @property
    def avatar_url(self):
        if self.profile_photo and hasattr(self.profile_photo, 'url'):
            return self.profile_photo.url
        name = self.get_full_name() or self.username
        return f"https://ui-avatars.com/api/?name={name}&background=0284c7&color=ffffff&bold=true"

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
