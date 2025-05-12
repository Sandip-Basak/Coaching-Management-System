from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import (
    User, StudentProfile, Course, Batch, Question, Option, 
    PracticePaper, MockExam, Attempt, Answer, CourseMaterial
)


class StudentProfileInline(admin.StackedInline):
    model = StudentProfile
    can_delete = False
    verbose_name_plural = 'Student Profile'


class CustomUserAdmin(UserAdmin):
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'is_student', 'is_admin_staff')
    list_filter = ('is_staff', 'is_student', 'is_admin_staff')
    fieldsets = UserAdmin.fieldsets + (
        ('Custom Fields', {'fields': ('is_student', 'is_admin_staff')}),
    )
    inlines = [StudentProfileInline]


class StudentProfileAdmin(admin.ModelAdmin):
    list_display = ('get_username', 'approved', 'get_profile_photo')
    list_filter = ('approved',)
    search_fields = ('user__username', 'user__email')
    actions = ['approve_students', 'disapprove_students']
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    def get_profile_photo(self, obj):
        if obj.profile_photo:
            return format_html('<img src="{}" width="50" height="50" />', obj.profile_photo.url)
        return "-"
    get_profile_photo.short_description = 'Profile Photo'
    
    def approve_students(self, request, queryset):
        queryset.update(approved=True)
    approve_students.short_description = "Approve selected students"
    
    def disapprove_students(self, request, queryset):
        queryset.update(approved=False)
    disapprove_students.short_description = "Disapprove selected students"


class BatchInline(admin.TabularInline):
    model = Batch
    extra = 1


class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')
    prepopulated_fields = {'slug': ('name',)}
    inlines = [BatchInline]


class BatchAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'start_date', 'end_date')
    list_filter = ('course',)
    filter_horizontal = ('students',)


class OptionInline(admin.TabularInline):
    model = Option
    extra = 4


class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'marks', 'multiple_correct')
    inlines = [OptionInline]


class OptionAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)


class PracticePaperAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'created_by', 'allowed_for_trial', 'time_limit')
    list_filter = ('course', 'allowed_for_trial')
    filter_horizontal = ('questions',)


class MockExamAdmin(admin.ModelAdmin):
    list_display = ('name', 'course', 'created_by', 'time_limit', 'results_released')
    list_filter = ('course', 'results_released')
    filter_horizontal = ('questions',)
    actions = ['release_results', 'hide_results']
    
    def release_results(self, request, queryset):
        queryset.update(results_released=True)
    release_results.short_description = "Release results for selected exams"
    
    def hide_results(self, request, queryset):
        queryset.update(results_released=False)
    hide_results.short_description = "Hide results for selected exams"


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 0


class AttemptAdmin(admin.ModelAdmin):
    list_display = ('get_user', 'get_paper', 'attempt_type', 'start_time', 'end_time', 'status', 'score')
    list_filter = ('status', 'attempt_type')
    inlines = [AnswerInline]
    
    def get_user(self, obj):
        return obj.user.username if obj.user else "Trial User"
    get_user.short_description = 'User'
    
    def get_paper(self, obj):
        if obj.attempt_type == 'practice':
            return obj.practice_paper.name
        else:
            return obj.mock_exam.name
    get_paper.short_description = 'Paper/Exam'


class AnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question')
    filter_horizontal = ('selected_options',)


class CourseMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'material_type', 'batch', 'uploaded_by', 'uploaded_at')
    list_filter = ('material_type', 'batch')
    search_fields = ('title', 'description')


admin.site.register(User, CustomUserAdmin)
admin.site.register(StudentProfile, StudentProfileAdmin)
admin.site.register(Course, CourseAdmin)
admin.site.register(Batch, BatchAdmin)
admin.site.register(Question, QuestionAdmin)
admin.site.register(Option, OptionAdmin)
admin.site.register(PracticePaper, PracticePaperAdmin)
admin.site.register(MockExam, MockExamAdmin)
admin.site.register(Attempt, AttemptAdmin)
admin.site.register(Answer, AnswerAdmin)
admin.site.register(CourseMaterial, CourseMaterialAdmin)
