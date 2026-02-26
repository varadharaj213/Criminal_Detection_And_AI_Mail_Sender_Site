from django.urls import path, include
from .views import *

urlpatterns = [
    path('', home, name='home'),
    path('ajax/', ajax, name='ajax'),
    path('scan/', scan, name='scan'),
    path('save-location/', save_location, name='save_location'),
    path('profiles/', profiles, name='profiles'),
    path('details/', details, name='details'),
    path('add_profile/', add_profile, name='add_profile'),
    path('edit_profile/<int:id>/', edit_profile, name='edit_profile'),
    path('delete_profile/<int:id>/', delete_profile, name='delete_profile'),
    path('clear_history/', clear_history, name='clear_history'),
    
    # Audio detection URLs
    path('start-audio-detection/', audio_detection, name='start_audio_detection'),
    path('stop-audio-detection/', stop_audio_detection, name='stop_audio_detection'),
    path('audio-alerts/', audio_alerts, name='audio_alerts'),
    path('clear-audio-alerts/', clear_audio_alerts, name='clear_audio_alerts'),
]