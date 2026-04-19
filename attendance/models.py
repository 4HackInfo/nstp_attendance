from django.db import models
from accounts.models import StudentProfile, User
from django.utils import timezone

class AttendanceRecord(models.Model):
    STATUS_CHOICES = [
        ('present', 'Present'),
        ('absent', 'Absent'),
        ('late', 'Late'),
        ('cutting', 'Cutting'),
    ]
    
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField()
    time_in = models.DateTimeField(null=True, blank=True)
    time_out = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='absent')
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_attendances')
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'date']
        ordering = ['-date', '-time_in']
    
    def __str__(self):
        return f"{self.student.preferred_number} - {self.student.first_name} - {self.date}"
    
    def save(self, *args, **kwargs):
        # Determine status based on time_in and time_out presence
        if self.time_in and self.time_out:
            self.status = 'present'
        elif self.time_in and not self.time_out:
            self.status = 'cutting'
        elif not self.time_in and self.time_out:
            self.status = 'late'
        else:
            self.status = 'absent'
        
        super().save(*args, **kwargs)
    
    @property
    def has_time_in(self):
        return self.time_in is not None
    
    @property
    def has_time_out(self):
        return self.time_out is not None


class PendingAttendance(models.Model):
    ACTION_CHOICES = [
        ('time_in', 'Time In'),
        ('time_out', 'Time Out'),
    ]
    
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    is_confirmed = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"PENDING: {self.student.preferred_number} - {self.action} - {self.timestamp}"
    
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    def confirm(self):
        """Confirm and save to AttendanceRecord"""
        today = timezone.now().date()
        
        # Get or create attendance record
        attendance, created = AttendanceRecord.objects.get_or_create(
            student=self.student,
            date=today,
            defaults={'recorded_by': self.recorded_by}
        )
        
        if self.action == 'time_in':
            if not attendance.time_in:
                attendance.time_in = self.timestamp
                attendance.recorded_by = self.recorded_by
                attendance.save()
                
                # Create log
                AttendanceLog.objects.create(
                    student=self.student,
                    action='time_in',
                    recorded_by=self.recorded_by
                )
        else:  # time_out
            if not attendance.time_out:
                attendance.time_out = self.timestamp
                attendance.recorded_by = self.recorded_by
                attendance.save()
                
                # Create log
                AttendanceLog.objects.create(
                    student=self.student,
                    action='time_out',
                    recorded_by=self.recorded_by
                )
        
        self.is_confirmed = True
        self.save()
        return attendance


class AttendanceLog(models.Model):
    ACTION_CHOICES = [
        ('time_in', 'Time In'),
        ('time_out', 'Time Out'),
        ('override', 'Override'),
    ]
    
    student = models.ForeignKey(StudentProfile, on_delete=models.CASCADE)
    action = models.CharField(max_length=20, choices=ACTION_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)
    recorded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        ordering = ['-timestamp']
    
    def __str__(self):
        return f"{self.student.preferred_number} - {self.action} - {self.timestamp}"