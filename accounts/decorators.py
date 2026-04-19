from django.shortcuts import redirect
from django.contrib.auth.decorators import user_passes_test
from django.core.exceptions import PermissionDenied

def student_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.user_type != 'student':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def instructor_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.user_type != 'instructor':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view

def admin_staff_required(view_func):
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('login')
        if request.user.user_type != 'admin_staff':
            raise PermissionDenied
        return view_func(request, *args, **kwargs)
    return _wrapped_view