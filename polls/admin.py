from django.contrib import admin

# Register your models here.

from .models import Question, Answer
from django.contrib.auth.models import User


class AnwserInline(admin.TabularInline):
    model = Answer
    extra = 0


class QuestionAdmin(admin.ModelAdmin):
    fieldsets = [
        ('题型及内容', {'fields': ['question_name', 'question_content']}),
        ('日期',      {'fields': ['date'], 'classes':['collapse']}),
    ]
    list_display = ('question_name', 'question_content', 'date')
    list_filter = ['date']
    search_fields = ['question_content']
    inlines = [AnwserInline]


admin.site.register(Question, QuestionAdmin)

