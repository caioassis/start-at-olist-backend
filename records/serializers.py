from rest_framework.serializers import (ModelSerializer, Serializer, DateTimeField, CharField, DecimalField,
                                        SerializerMethodField)
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
    start = DateTimeField()
    end = DateTimeField()
    call_id = CharField()
    destination = CharField()
    duration = SerializerMethodField()
    price = DecimalField(max_digits=10, decimal_places=2)

    def get_duration(self, obj):
        """
        Format duration from seconds to h m s.
        """
        duration = int(obj['duration'])
        hours, duration = divmod(duration, 60 * 60)
        minutes, duration = divmod(duration, 60)
        seconds = duration
        return f'{hours}h{minutes}m{seconds}s'
