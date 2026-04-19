from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.views.decorators.http import require_POST
from accounts.decorators import instructor_required, admin_staff_required
from accounts.models import StudentProfile
from .models import AttendanceRecord, AttendanceLog, PendingAttendance
from .forms import PreferredNumberForm, FilterForm
import csv
from datetime import datetime, timedelta
from django.db import transaction
import threading
import json


@login_required
@admin_staff_required
def admin_dashboard(request):
    today = timezone.now().date()
    total_students = StudentProfile.objects.count()
    
    # Get today's attendance records
    today_attendance = AttendanceRecord.objects.filter(date=today)
    
    # Count different statuses
    present_today = today_attendance.filter(status='present').count()
    absent_today = today_attendance.filter(status='absent').count()
    late_today = today_attendance.filter(status='late').count()
    cutting_today = today_attendance.filter(status='cutting').count()
    
    context = {
        'total_students': total_students,
        'present_today': present_today,
        'absent_today': absent_today,
        'late_today': late_today,
        'cutting_today': cutting_today,
    }
    return render(request, 'admin_dashboard/dashboard.html', context)


def auto_confirm_attendance(pending_id):
    """Background task to auto-confirm pending attendance after 15 seconds"""
    import time
    time.sleep(15)
    
    try:
        pending = PendingAttendance.objects.get(id=pending_id, is_confirmed=False)
        if not pending.is_expired():
            pending.confirm()
    except PendingAttendance.DoesNotExist:
        pass  # Already cancelled or confirmed


@login_required
@admin_staff_required
def time_in_view(request):
    if request.method == 'POST':
        form = PreferredNumberForm(request.POST)
        if form.is_valid():
            number = form.cleaned_data['preferred_number']
            try:
                student = StudentProfile.objects.get(preferred_number=number)
                today = timezone.now().date()
                current_time = timezone.now()
                
                # Check if already timed in today
                existing_attendance = AttendanceRecord.objects.filter(
                    student=student,
                    date=today,
                    time_in__isnull=False
                ).first()
                
                if existing_attendance:
                    messages.warning(
                        request, 
                        f'{student.first_name} {student.last_name} already timed in today at {existing_attendance.time_in.strftime("%I:%M %p")}!'
                    )
                    return redirect('time_in')
                
                # Check if there's already a pending time-in
                existing_pending = PendingAttendance.objects.filter(
                    student=student,
                    action='time_in',
                    is_confirmed=False
                ).first()
                
                if existing_pending:
                    # If expired, delete it
                    if existing_pending.is_expired():
                        existing_pending.delete()
                    else:
                        messages.warning(
                            request,
                            f'There is already a pending time-in for {student.first_name} {student.last_name}. '
                        )
                        return redirect('time_in')
                
                # Create pending attendance
                expires_at = current_time + timedelta(seconds=15)
                pending = PendingAttendance.objects.create(
                    student=student,
                    action='time_in',
                    recorded_by=request.user,
                    expires_at=expires_at
                )
                
                messages.success(
                    request,
                    f'Time In recorded for {student.first_name} {student.last_name} (#{student.preferred_number}). '
                )
                
                return redirect('time_in')
                
            except StudentProfile.DoesNotExist:
                messages.error(request, f'No student found with preferred number {number}')
    else:
        form = PreferredNumberForm()
    
    # Clean up expired pending records
    PendingAttendance.objects.filter(
        expires_at__lt=timezone.now(),
        is_confirmed=False
    ).delete()
    
    # Get pending time-ins
    pending_timeins = PendingAttendance.objects.filter(
        action='time_in',
        is_confirmed=False
    ).order_by('-timestamp')
    
    # Get confirmed time-ins for today
    today = timezone.now().date()
    confirmed_attendance = AttendanceRecord.objects.filter(
        date=today, 
        time_in__isnull=False
    ).order_by('-time_in')[:20]
    
    return render(request, 'admin_dashboard/timein.html', {
        'form': form,
        'pending_timeins': pending_timeins,
        'confirmed_attendance': confirmed_attendance,
    })

@login_required
@admin_staff_required
def time_out_view(request):
    if request.method == 'POST':
        form = PreferredNumberForm(request.POST)
        if form.is_valid():
            number = form.cleaned_data['preferred_number']
            try:
                student = StudentProfile.objects.get(preferred_number=number)
                today = timezone.now().date()
                current_time = timezone.now()
                
                # Check if already timed out today
                existing_attendance = AttendanceRecord.objects.filter(
                    student=student,
                    date=today,
                    time_out__isnull=False
                ).first()
                
                if existing_attendance:
                    messages.warning(
                        request, 
                        f'{student.first_name} {student.last_name} already timed out today at {existing_attendance.time_out.strftime("%I:%M %p")}!'
                    )
                    return redirect('time_out')
                
                # Check if there's already a pending time-out
                existing_pending = PendingAttendance.objects.filter(
                    student=student,
                    action='time_out',
                    is_confirmed=False
                ).first()
                
                if existing_pending:
                    # If expired, delete it
                    if existing_pending.is_expired():
                        existing_pending.delete()
                    else:
                        messages.warning(
                            request,
                            f'There is already a pending time-out for {student.first_name} {student.last_name}. '
                        )
                        return redirect('time_out')
                
                # Create pending attendance
                expires_at = current_time + timedelta(seconds=15)
                pending = PendingAttendance.objects.create(
                    student=student,
                    action='time_out',
                    recorded_by=request.user,
                    expires_at=expires_at
                )
                
                messages.success(
                    request,
                    f'Time Out recorded for {student.first_name} {student.last_name} (#{student.preferred_number}). '
                )
                
                return redirect('time_out')
                
            except StudentProfile.DoesNotExist:
                messages.error(request, f'No student found with preferred number {number}')
    else:
        form = PreferredNumberForm()
    
    # Clean up expired pending records
    PendingAttendance.objects.filter(
        expires_at__lt=timezone.now(),
        is_confirmed=False
    ).delete()
    
    # Get pending time-outs
    pending_timeouts = PendingAttendance.objects.filter(
        action='time_out',
        is_confirmed=False
    ).order_by('-timestamp')
    
    # Get confirmed time-outs for today
    today = timezone.now().date()
    confirmed_attendance = AttendanceRecord.objects.filter(
        date=today, 
        time_out__isnull=False
    ).order_by('-time_out')[:20]
    
    return render(request, 'admin_dashboard/timeout.html', {
        'form': form,
        'pending_timeouts': pending_timeouts,
        'confirmed_attendance': confirmed_attendance,
    })

@require_POST
@login_required
@admin_staff_required
def confirm_pending(request, pending_id):
    """Confirm and save pending attendance to database"""
    try:
        pending = PendingAttendance.objects.get(
            id=pending_id,
            is_confirmed=False
        )
        
        attendance = pending.confirm()
        
        return JsonResponse({
            'success': True,
            'message': f'{pending.get_action_display()} saved for {pending.student.first_name} {pending.student.last_name}',
            'status': attendance.status
        })
    except PendingAttendance.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Pending record not found or already saved.'
        })
    

@login_required
@instructor_required
def instructor_dashboard(request):
    # Get filter parameters from GET request
    company_filter = request.GET.get('company', '')
    course_filter = request.GET.get('course', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    # Set the date to filter (default to today)
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            filter_date = timezone.now().date()
    else:
        filter_date = timezone.now().date()
    
    # Start with all students
    students = StudentProfile.objects.all().select_related('user')
    
    # Apply company filter
    if company_filter:
        students = students.filter(company=company_filter)
    
    # Apply course filter
    if course_filter:
        students = students.filter(course=course_filter)
    
    # Get attendance records for the filtered date
    attendance_records = AttendanceRecord.objects.filter(
        date=filter_date
    ).select_related('student')
    
    # Create a dictionary of attendance records by student ID for quick lookup
    attendance_dict = {
        record.student_id: record for record in attendance_records
    }
    
    # Prepare attendance data and calculate statistics
    attendance_data = []
    stats = {
        'present': 0,
        'absent': 0,
        'late': 0,
        'cutting': 0
    }
    
    for student in students:
        # Get attendance record for this student on the filtered date
        attendance = attendance_dict.get(student.id)
        
        if attendance:
            status = attendance.status
            time_in = attendance.time_in
            time_out = attendance.time_out
        else:
            # No attendance record means absent
            status = 'absent'
            time_in = None
            time_out = None
        
        # Update statistics
        stats[status] = stats.get(status, 0) + 1
        
        # Apply status filter
        if status_filter and status != status_filter:
            continue
        
        attendance_data.append({
            'student': student,
            'status': status,
            'time_in': time_in,
            'time_out': time_out,
            'date': filter_date,
        })
    
    # Create form with current filter values
    form = FilterForm(initial={
        'company': company_filter,
        'course': course_filter,
        'status': status_filter,
        'date': filter_date,
    })
    
    context = {
        'form': form,
        'attendance_data': attendance_data,
        'filter_date': filter_date,
        'total_records': len(attendance_data),
        'stats': stats,
    }
    
    return render(request, 'instructor/dashboard.html', context)

@login_required
@instructor_required
def export_csv(request):
    # Get filter parameters from GET request
    company_filter = request.GET.get('company', '')
    course_filter = request.GET.get('course', '')
    status_filter = request.GET.get('status', '')
    date_filter = request.GET.get('date', '')
    
    # Get sort parameters
    sort_column = request.GET.get('sort', 'name')  # Default sort by name
    sort_direction = request.GET.get('direction', 'asc')  # Default ascending
    
    # Set the date to filter (default to today)
    if date_filter:
        try:
            filter_date = datetime.strptime(date_filter, '%Y-%m-%d').date()
        except ValueError:
            filter_date = timezone.now().date()
    else:
        filter_date = timezone.now().date()
    
    # Start with all students
    students = StudentProfile.objects.all().select_related('user')
    
    # Apply filters
    if company_filter:
        students = students.filter(company=company_filter)
    if course_filter:
        students = students.filter(course=course_filter)
    
    # Get attendance records for the filtered date
    attendance_records = AttendanceRecord.objects.filter(
        date=filter_date
    ).select_related('student')
    
    # Create a dictionary of attendance records by student ID
    attendance_dict = {
        record.student_id: record for record in attendance_records
    }
    
    # Prepare data list for sorting
    export_data = []
    
    for student in students:
        attendance = attendance_dict.get(student.id)
        
        if attendance:
            status = attendance.status
            time_in = attendance.time_in
            time_out = attendance.time_out
            time_in_str = attendance.time_in.strftime('%I:%M %p') if attendance.time_in else 'N/A'
            time_out_str = attendance.time_out.strftime('%I:%M %p') if attendance.time_out else 'N/A'
            time_in_sort = attendance.time_in.isoformat() if attendance.time_in else ''
            time_out_sort = attendance.time_out.isoformat() if attendance.time_out else ''
        else:
            status = 'absent'
            time_in = None
            time_out = None
            time_in_str = 'N/A'
            time_out_str = 'N/A'
            time_in_sort = ''
            time_out_sort = ''
        
        # Apply status filter
        if status_filter and status != status_filter:
            continue
        
        export_data.append({
            'student_id': student.student_id,
            'name': f"{student.last_name}, {student.first_name}",
            'first_name': student.first_name,
            'last_name': student.last_name,
            'course': student.get_course_display(),
            'company': student.get_company_display(),
            'year_level': student.get_year_level_display(),
            'status': status.capitalize(),
            'status_sort': status,
            'time_in': time_in_str,
            'time_out': time_out_str,
            'time_in_sort': time_in_sort,
            'time_out_sort': time_out_sort,
            'date': filter_date.strftime('%Y-%m-%d'),
        })
    
    # Sort the data based on sort parameters
    status_order = {'present': 1, 'late': 2, 'cutting': 3, 'absent': 4}
    
    def get_sort_key(item):
        if sort_column == 'student_id':
            return item['student_id']
        elif sort_column == 'name':
            return f"{item['last_name']} {item['first_name']}".lower()
        elif sort_column == 'course':
            return item['course'].lower()
        elif sort_column == 'company':
            return item['company'].lower()
        elif sort_column == 'year':
            return item['year_level']
        elif sort_column == 'status':
            return status_order.get(item['status_sort'], 5)
        elif sort_column == 'timeIn':
            return item['time_in_sort'] if item['time_in_sort'] else '9' * 20  # Empty times go to end
        elif sort_column == 'timeOut':
            return item['time_out_sort'] if item['time_out_sort'] else '9' * 20
        else:
            return f"{item['last_name']} {item['first_name']}".lower()
    
    # Sort the data
    reverse_sort = (sort_direction == 'desc')
    
    if sort_column == 'timeIn' or sort_column == 'timeOut':
        # For time fields, handle empty values specially
        if sort_direction == 'asc':
            export_data.sort(key=lambda x: (x[f'{sort_column}_sort'] == '', x[f'{sort_column}_sort']))
        else:
            export_data.sort(key=lambda x: (x[f'{sort_column}_sort'] == '', x[f'{sort_column}_sort']), reverse=True)
    else:
        export_data.sort(key=get_sort_key, reverse=reverse_sort)
    
    # Create HTTP response with CSV content
    response = HttpResponse(content_type='text/csv')
    
    # Generate filename with filter info
    filename_parts = [f"attendance_{filter_date.strftime('%Y%m%d')}"]
    if company_filter:
        filename_parts.append(f"company_{company_filter}")
    if course_filter:
        filename_parts.append(f"course_{course_filter}")
    if status_filter:
        filename_parts.append(f"status_{status_filter}")
    filename_parts.append(f"sorted_by_{sort_column}_{sort_direction}")
    
    filename = "_".join(filename_parts) + ".csv"
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header with filter information
    writer.writerow(['NSTP ATTENDANCE REPORT'])
    writer.writerow([f'Date: {filter_date.strftime("%B %d, %Y")}'])
    
    filter_info = []
    if company_filter:
        filter_info.append(f'Company: {dict(StudentProfile.COMPANIES).get(company_filter, company_filter)}')
    if course_filter:
        filter_info.append(f'Course: {dict(StudentProfile.COURSES).get(course_filter, course_filter)}')
    if status_filter:
        filter_info.append(f'Status: {status_filter.capitalize()}')
    if filter_info:
        writer.writerow([f'Filters: {" | ".join(filter_info)}'])
    
    writer.writerow([f'Sorted by: {sort_column.replace("_", " ").title()} ({sort_direction.upper()})'])
    writer.writerow([])  # Empty row
    
    # Write column headers
    writer.writerow([
        'Student ID', 
        'Last Name',
        'First Name',
        'Full Name',
        'Course', 
        'Company', 
        'Year Level', 
        'Status', 
        'Time In', 
        'Time Out', 
        'Date'
    ])
    
    # Write data rows
    for item in export_data:
        writer.writerow([
            item['student_id'],
            item['last_name'],
            item['first_name'],
            item['name'],
            item['course'],
            item['company'],
            item['year_level'],
            item['status'],
            item['time_in'],
            item['time_out'],
            item['date'],
        ])
    
    # Write summary
    writer.writerow([])
    writer.writerow(['SUMMARY'])
    
    status_counts = {'Present': 0, 'Absent': 0, 'Late': 0, 'Cutting': 0}
    for item in export_data:
        status_counts[item['status']] += 1
    
    writer.writerow(['Total Records:', len(export_data)])
    for status, count in status_counts.items():
        writer.writerow([f'{status}:', count])
    
    return response


@login_required
@instructor_required
def override_attendance(request, student_id):
    if request.method == 'POST':
        student = get_object_or_404(StudentProfile, id=student_id)
        date_str = request.POST.get('date', '')
        status = request.POST.get('status', 'present')
        notes = request.POST.get('notes', '')
        
        # Parse the date
        if date_str:
            try:
                date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                date = timezone.now().date()
        else:
            date = timezone.now().date()
        
        # Get or create attendance record
        attendance, created = AttendanceRecord.objects.get_or_create(
            student=student,
            date=date,
            defaults={
                'status': status,
                'recorded_by': request.user,
                'notes': notes
            }
        )
        
        if not created:
            attendance.status = status
            attendance.notes = notes
            attendance.recorded_by = request.user
            attendance.save()
        
        # Log the override
        AttendanceLog.objects.create(
            student=student,
            action='override',
            recorded_by=request.user,
            notes=f"Status overridden to {status}. {notes}"
        )
        
        messages.success(request, f'Attendance overridden for {student.first_name} {student.last_name} to {status.upper()}')
    
    return redirect('instructor_dashboard')

@require_POST
@login_required
@admin_staff_required
def cancel_pending(request, pending_id):
    """Cancel a pending attendance entry (UNDO)"""
    try:
        pending = PendingAttendance.objects.get(
            id=pending_id,
            is_confirmed=False
        )
        
        student_name = f"{pending.student.first_name} {pending.student.last_name}"
        action = pending.get_action_display()
        
        pending.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'{action} for {student_name} has been cancelled.'
        })
    except PendingAttendance.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Record already saved or cancelled.'
        })


@require_POST
@login_required
@admin_staff_required
def confirm_now(request, pending_id):
    """Manually confirm a pending attendance immediately"""
    try:
        pending = PendingAttendance.objects.get(
            id=pending_id,
            is_confirmed=False,
            recorded_by=request.user
        )
        
        attendance = pending.confirm()
        
        return JsonResponse({
            'success': True,
            'message': f'{pending.get_action_display()} confirmed for {pending.student.first_name} {pending.student.last_name}',
            'status': attendance.status
        })
    except PendingAttendance.DoesNotExist:
        return JsonResponse({
            'success': False,
            'message': 'Pending record not found.'
        })

@login_required
@admin_staff_required
def get_pending_status(request):
    """Get current pending items for real-time updates"""
    pending_timeins = PendingAttendance.objects.filter(
        action='time_in',
        is_confirmed=False,
        expires_at__gt=timezone.now()
    ).select_related('student')
    
    pending_timeouts = PendingAttendance.objects.filter(
        action='time_out',
        is_confirmed=False,
        expires_at__gt=timezone.now()
    ).select_related('student')
    
    data = {
        'timeins': [{
            'id': p.id,
            'student_name': f"{p.student.first_name} {p.student.last_name}",
            'preferred_number': p.student.preferred_number,
            'timestamp': p.timestamp.strftime('%I:%M:%S %p'),
            'expires_in': max(0, int((p.expires_at - timezone.now()).total_seconds()))
        } for p in pending_timeins],
        'timeouts': [{
            'id': p.id,
            'student_name': f"{p.student.first_name} {p.student.last_name}",
            'preferred_number': p.student.preferred_number,
            'timestamp': p.timestamp.strftime('%I:%M:%S %p'),
            'expires_in': max(0, int((p.expires_at - timezone.now()).total_seconds()))
        } for p in pending_timeouts]
    }
    
    return JsonResponse(data)
