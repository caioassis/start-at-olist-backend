from django.urls import path
from .views import CallStartRecordAPIView, CallEndRecordAPIView, TelephonyBillAPIView

urlpatterns = [
    path('started/', CallStartRecordAPIView.as_view()),
    path('finished/', CallEndRecordAPIView.as_view()),
    path('bills/', TelephonyBillAPIView.as_view())
]