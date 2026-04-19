from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, StudentProfile, InstructorProfile, AdminStaffProfile

class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'user_type', 'is_staff')
    list_filter = ('user_type', 'is_staff', 'is_superuser')
    fieldsets = UserAdmin.fieldsets + (
        ('User Type', {'fields': ('user_type',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('User Type', {'fields': ('user_type',)}),
    )

@admin.register(StudentProfile)
class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('preferred_number', 'first_name', 'last_name', 'student_id', 'course', 'company', 'year_level')
    list_filter = ('course', 'company', 'year_level')
    search_fields = ('first_name', 'last_name', 'student_id', 'preferred_number')
    readonly_fields = ('preferred_number',)

@admin.register(InstructorProfile)
class InstructorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'department', 'employee_id')
    search_fields = ('user__username', 'employee_id')

@admin.register(AdminStaffProfile)
class AdminStaffProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'role', 'staff_id')
    search_fields = ('user__username', 'staff_id')

admin.site.register(User, CustomUserAdmin)