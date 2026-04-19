from django.db import models
from django.contrib.auth.models import AbstractUser

class User(AbstractUser):
    USER_TYPES = (
        ('student', 'Student'),
        ('instructor', 'Instructor'),
        ('admin_staff', 'Admin Staff'),
    )
    user_type = models.CharField(max_length=20, choices=USER_TYPES, default='student')
    email = models.EmailField(unique=True)
    
    def __str__(self):
        return f"{self.username} - {self.user_type}"

class StudentProfile(models.Model):
    COURSES = [
        ('BSIT', 'BSIT - Information Technology'),
        ('BSED', 'BSED - Education'),
        ('BSHM', 'BSHM - Hospitality Management'),
        ('BSCRIM', 'BSCRIM - Criminology'),
        ('BSTM', 'BSTM - Tourism Management'),
    ]
    
    YEAR_LEVELS = [
        ('1', '1st Year'),
        ('2', '2nd Year'),
        ('3', '3rd Year'),
        ('4', '4th Year'),
    ]
    
    COMPANIES = [
        ('ALPHA', 'Alpha'),
        ('BRAVO', 'Bravo'),
        ('CHARLIE', 'Charlie'),
        ('DELTA', 'Delta'),
        ('ECHO', 'Echo'),
        ('FOXTROT', 'Foxtrot'),
        ('GOLF', 'Golf'),
        ('HOTEL', 'Hotel'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_profile')
    student_id = models.CharField(max_length=20, unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    course = models.CharField(max_length=20, choices=COURSES)
    year_level = models.CharField(max_length=2, choices=YEAR_LEVELS, default='1')
    company = models.CharField(max_length=20, choices=COMPANIES)
    preferred_number = models.IntegerField(unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.preferred_number} - {self.first_name} {self.last_name}"
    
    def save(self, *args, **kwargs):
        if not self.preferred_number:
            last_profile = StudentProfile.objects.order_by('-preferred_number').first()
            self.preferred_number = 1 if not last_profile else last_profile.preferred_number + 1
        super().save(*args, **kwargs)

class InstructorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='instructor_profile')
    department = models.CharField(max_length=100, default='General')
    employee_id = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.department}"

class AdminStaffProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    role = models.CharField(max_length=100, default='Task Force')
    staff_id = models.CharField(max_length=20, unique=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.role}"