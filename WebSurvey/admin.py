from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Section

# Register your models here.

class SectionInline(admin.TabularInline):
    model = Section
    extra = 0

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role',)}),
    )

    # Show sections when editing a teacher
    inlines = [SectionInline]

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'teacher']
    search_fields = ['name', 'teacher__username']
