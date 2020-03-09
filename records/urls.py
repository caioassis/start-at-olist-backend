from django.urls import path
from .views import CallStartRecordAPIView, CallEndRecordAPIView

urlpatterns = [
    path('started/', CallStartRecordAPIView.as_view()),
    path('finished/', CallEndRecordAPIView.as_view())
]
