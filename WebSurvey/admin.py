from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    User, Section, Survey, Question, MultipleChoiceOption,
    TrueFalseAnswer, EnumerationAnswer,
    StudentResponse, QuestionAnswer
)

# Register your models here.

class SectionInline(admin.TabularInline):
    model = Section
    extra = 0

@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'role', 'is_staff']
    list_filter = ['role', 'is_staff', 'is_superuser', 'is_active']
    fieldsets = UserAdmin.fieldsets + (
        ('Role Information', {'fields': ('role', 'section')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ('Role Information', {'fields': ('role', 'section')}),
    )

    # Show sections when editing a teacher
    inlines = [SectionInline]

@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'teacher']
    search_fields = ['name', 'teacher__username']


@admin.register(Survey)
class SurveyAdmin(admin.ModelAdmin):
    list_display = ['title', 'teacher', 'status', 'total_points', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'description', 'teacher__username']
    filter_horizontal = ['sections']


class MultipleChoiceOptionInline(admin.TabularInline):
    model = MultipleChoiceOption
    extra = 1


class TrueFalseAnswerInline(admin.StackedInline):
    model = TrueFalseAnswer
    extra = 0


class EnumerationAnswerInline(admin.TabularInline):
    model = EnumerationAnswer
    extra = 1


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['question_text', 'survey', 'question_type', 'points', 'order']
    list_filter = ['question_type', 'survey']
    search_fields = ['question_text', 'survey__title']
    inlines = [MultipleChoiceOptionInline, TrueFalseAnswerInline, EnumerationAnswerInline]


@admin.register(StudentResponse)
class StudentResponseAdmin(admin.ModelAdmin):
    list_display = ['student', 'survey', 'score', 'is_submitted', 'submitted_at']
    list_filter = ['is_submitted', 'submitted_at']
    search_fields = ['student__username', 'survey__title']


@admin.register(QuestionAnswer)
class QuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ['response', 'question', 'points_earned', 'is_correct']
    list_filter = ['is_correct']
    search_fields = ['response__student__username', 'question__question_text']

