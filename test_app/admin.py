from django.contrib import admin
from django.utils.html import format_html
from .models import Level, TestSession, Question, Answer, TestResult

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4
    max_num = 6

@admin.register(Level)
class LevelAdmin(admin.ModelAdmin):
    list_display = ('name', 'code', 'order', 'time_limit', 'question_count', 'is_active')
    list_editable = ('order', 'time_limit', 'question_count', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name', 'code')
    ordering = ('order',)

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('level', 'short_question_text', 'has_image', 'is_active')
    list_filter = ('level', 'is_active')
    search_fields = ('question_text',)
    inlines = [AnswerInline]
    
    def short_question_text(self, obj):
        return obj.question_text[:100] + '...' if len(obj.question_text) > 100 else obj.question_text
    short_question_text.short_description = 'Savol'
    
    def has_image(self, obj):
        return bool(obj.image)
    has_image.boolean = True
    has_image.short_description = 'Rasm'

@admin.register(TestSession)
class TestSessionAdmin(admin.ModelAdmin):
    list_display = ('session_id', 'full_name', 'level', 'start_time', 'completed')
    list_filter = ('level', 'completed', 'start_time')
    search_fields = ('first_name', 'last_name', 'phone_number', 'session_id')
    readonly_fields = ('session_id', 'start_time', 'end_time')
    
    def full_name(self, obj):
        return f"{obj.first_name} {obj.last_name}"
    full_name.short_description = 'Ism Familya'

@admin.register(TestResult)
class TestResultAdmin(admin.ModelAdmin):
    list_display = ('session_info', 'level', 'score', 'correct_answers', 'time_taken_display', 'telegram_sent', 'admin_notified', 'created_at')
    list_filter = ('telegram_sent', 'admin_notified', 'session__level', 'created_at')
    search_fields = ('session__first_name', 'session__last_name', 'session__session_id')
    readonly_fields = ('created_at',)
    
    def session_info(self, obj):
        return f"{obj.session.first_name} {obj.session.last_name}"
    session_info.short_description = 'Ishtirokchi'
    
    def level(self, obj):
        return obj.session.level.name if obj.session.level else '-'
    level.short_description = 'Daraja'
    
    def time_taken_display(self, obj):
        return obj.get_time_taken_display()
    time_taken_display.short_description = 'Sarflangan vaqt'

admin.site.register(Answer)