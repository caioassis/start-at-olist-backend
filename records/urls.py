from django.urls import path
from rest_framework.routers import SimpleRouter
from .views import CallEndRecordAPIView, CallStartRecordAPIView, TelephonyBillViewSet

router = SimpleRouter()

router.register('bills', TelephonyBillViewSet, basename='bills')

urlpatterns = [
    path('started/', CallStartRecordAPIView.as_view(), name='call_start_record_create'),
    path('finished/', CallEndRecordAPIView.as_view(), name='call_end_record_create'),
] + router.urls
