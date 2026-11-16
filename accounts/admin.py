from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    model = User
    list_display = ('username', 'email', 'role', 'student_id', 'department', 'year_level', 'is_staff')
    list_filter = ('role', 'is_staff', 'is_superuser', 'year_level')
    fieldsets = UserAdmin.fieldsets + (
        ('BorrowTech Profile Details', {
            'fields': ('role', 'student_id', 'contact_number', 'department', 'year_level', 'profile_photo')
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('BorrowTech Profile Details', {
            'fields': ('role', 'student_id', 'contact_number', 'department', 'year_level', 'profile_photo')
        }),
    )
    search_fields = ('username', 'email', 'first_name', 'last_name', 'student_id')
    ordering = ('username',)
