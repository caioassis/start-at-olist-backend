from rest_framework.generics import CreateAPIView
from .serializers import CallStartRecordSerializer, CallEndRecordCreateSerializer


class CallStartRecordAPIView(CreateAPIView):
    serializer_class = CallStartRecordSerializer


class CallEndRecordAPIView(CreateAPIView):
    serializer_class = CallEndRecordCreateSerializer
