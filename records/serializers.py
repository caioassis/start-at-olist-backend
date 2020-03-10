from rest_framework.serializers import ModelSerializer, Serializer, DateTimeField, CharField, DecimalField
from .models import CallStartRecord, CallEndRecord


class CallStartRecordSerializer(ModelSerializer):

    class Meta:
        model = CallStartRecord
        fields = ['id', 'call_id', 'timestamp', 'source', 'destination']


class CallEndRecordCreateSerializer(ModelSerializer):

    class Meta:
        model = CallEndRecord
        fields = ['call_id']


class CallRecordSerializer(Serializer):
    """
    Serializer that gathers information from Call Start and Call End models.
    """
    start = CharField()
    end = CharField()
    call_id = CharField()
    source = CharField()
    destination = CharField()
    price = DecimalField(max_digits=10, decimal_places=2)
