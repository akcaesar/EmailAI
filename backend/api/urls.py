from django.urls import path
from .views import OllamaTestView

urlpatterns = [
    path('test-ollama/', OllamaTestView.as_view(), name='test-ollama'),
    # ... your existing URLs ...
]