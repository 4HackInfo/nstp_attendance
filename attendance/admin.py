from django.contrib import admin
from .models import AttendanceRecord, AttendanceLog

@admin.register(AttendanceRecord)
class AttendanceRecordAdmin(admin.ModelAdmin):
    list_display = ('student', 'date', 'time_in', 'time_out', 'status', 'recorded_by')
    list_filter = ('status', 'date', 'student__company', 'student__course')
    search_fields = ('student__first_name', 'student__last_name', 'student__student_id')
    date_hierarchy = 'date'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('student', 'recorded_by')

@admin.register(AttendanceLog)
class AttendanceLogAdmin(admin.ModelAdmin):
    list_display = ('student', 'action', 'timestamp', 'recorded_by')
    list_filter = ('action', 'timestamp')
    search_fields = ('student__first_name', 'student__last_name')
    date_hierarchy = 'timestamp'