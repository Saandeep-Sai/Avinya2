from django.urls import path
from . import views

urlpatterns = [
    path('upload-cover/', views.upload_cover, name='upload_cover'),
    path('upload-pdf/', views.upload_pdf, name='upload_pdf'),
    path('ask-question/', views.ask_question, name='ask_question'),
    path('', views.get_books, name='get_books'),
    path('<int:book_id>/', views.get_book_status, name='book_status'),
    path('<int:book_id>/chat-history/', views.get_chat_history, name='chat_history'),
    path('search/', views.search_books, name='search_books'),
    path('clear-all/', views.clear_all_books, name='clear_all_books'),
    path('check-plagiarism/', views.check_code_plagiarism, name='check_plagiarism'),
    path('batch-check-plagiarism/', views.batch_check_plagiarism, name='batch_check_plagiarism'),
]