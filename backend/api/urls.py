from django.urls import path
from .views import OllamaTestView, LandingView

urlpatterns = [
    path('test-ollama/', OllamaTestView.as_view(), name='test-ollama'),
    path('', LandingView.as_view(), name='landing'),
    # ... your existing URLs ...
]