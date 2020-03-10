from django.urls import path
from .views import CallEndRecordAPIView, CallStartRecordAPIView, TelephonyBillAPIView

urlpatterns = [
    path('started/', CallStartRecordAPIView.as_view(), name='call_start_record_create'),
    path('finished/', CallEndRecordAPIView.as_view(), name='call_end_record_create'),
    path('bills/', TelephonyBillAPIView.as_view(), name='get_telephony_bill')
]
