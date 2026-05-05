from django.urls import path
from .views import index

app_name = 'summarizer'

urlpatterns = [
    path('', index, name='index'),
]
