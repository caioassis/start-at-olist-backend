from rest_framework.serializers import ModelSerializer
from .models import CallStartRecord, CallEndRecord


class CallStartRecordSerializer(ModelSerializer):

    class Meta:
        model = CallStartRecord
        fields = ['id', 'call_id', 'timestamp', 'source', 'destination']


class CallEndRecordCreateSerializer(ModelSerializer):

    class Meta:
        model = CallEndRecord
        fields = ['call_id']
