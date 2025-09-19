from django.db import models
from django.contrib.auth.models import User

class Book(models.Model):
    title = models.CharField(max_length=255)
    author = models.CharField(max_length=255, blank=True, default='Unknown')
    cover_image = models.ImageField(upload_to='covers/', blank=True)
    pdf_file = models.FileField(upload_to='pdfs/', blank=True)
    extracted_text = models.TextField(blank=True)
    is_indexed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class Chat(models.Model):
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name='chats')
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
