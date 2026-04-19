from django.urls import path
from . import views

urlpatterns = [
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('time-in/', views.time_in_view, name='time_in'),
    path('time-out/', views.time_out_view, name='time_out'),
    path('instructor/dashboard/', views.instructor_dashboard, name='instructor_dashboard'),
    path('export-csv/', views.export_csv, name='export_csv'),
    path('override/<int:student_id>/', views.override_attendance, name='override_attendance'),
    path('confirm-pending/<int:pending_id>/', views.confirm_pending, name='confirm_pending'),
    path('cancel-pending/<int:pending_id>/', views.cancel_pending, name='cancel_pending'),
]