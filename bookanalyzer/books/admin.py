from django.contrib import admin
from .models import Book, Chat

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = ['title', 'author', 'is_indexed', 'created_at']
    list_filter = ['is_indexed', 'created_at']
    search_fields = ['title', 'author']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(Chat)
class ChatAdmin(admin.ModelAdmin):
    list_display = ['book', 'question', 'created_at']
    list_filter = ['created_at']
    search_fields = ['question', 'answer']
