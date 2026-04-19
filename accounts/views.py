from django.shortcuts import render

# Create your views here.
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import StudentRegistrationForm, CustomAuthenticationForm
from .decorators import student_required, instructor_required, admin_staff_required
from attendance.models import AttendanceRecord

def register_view(request):
    if request.method == 'POST':
        form = StudentRegistrationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                login(request, user)
                messages.success(request, f'Registration successful! Your preferred number is {user.student_profile.preferred_number}')
                return redirect('student_dashboard')
            except Exception as e:
                messages.error(request, f'Registration failed: {str(e)}')
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f'{field}: {error}')
    else:
        form = StudentRegistrationForm()
    return render(request, 'registration/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        form = CustomAuthenticationForm(data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f'Welcome back, {user.username}!')
            return redirect('dashboard_redirect')
    else:
        form = CustomAuthenticationForm()
    return render(request, 'registration/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, 'You have been logged out.')
    return redirect('login')

@login_required
def dashboard_redirect(request):
    if request.user.user_type == 'student':
        return redirect('student_dashboard')
    elif request.user.user_type == 'instructor':
        return redirect('instructor_dashboard')
    elif request.user.user_type == 'admin_staff':
        return redirect('admin_dashboard')
    return redirect('login')

@login_required
@student_required
def student_dashboard(request):
    try:
        student_profile = request.user.student_profile
        attendance_history = AttendanceRecord.objects.filter(student=student_profile).order_by('-date')
        
        context = {
            'student': student_profile,
            'attendance_history': attendance_history,
        }
        return render(request, 'student/dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Error loading dashboard: {str(e)}')
        return redirect('login')