from rest_framework.exceptions import ValidationError
from rest_framework.serializers import CharField, DateTimeField, DecimalField, ModelSerializer, Serializer
from .fields import DurationField
from .models import CallEndRecord, CallStartRecord


class CallStartRecordSerializer(ModelSerializer):

    class Meta:
        model = CallStartRecord
        fields = ['id', 'call_id', 'timestamp', 'source', 'destination']


class CallEndRecordCreateSerializer(ModelSerializer):

    def validate(self, attrs):
        validated_data = super().validate(attrs)
        timestamp = validated_data['timestamp']
        call_id = validated_data['call_id']
        try:
            call_start_record = CallStartRecord.objects.get(call_id=call_id)
        except CallStartRecord.DoesNotExist:
            raise ValidationError({'call_id': 'Given call_id does not exist.'})
        if timestamp < call_start_record.timestamp:
            raise ValidationError({'timestamp': 'Call end record timestamp cannot be earlier than call start record timestamp.'})
        return attrs

    class Meta:
        model = CallEndRecord
        fields = ['id', 'call_id', 'timestamp', 'price']
        read_only_fields = ['price']


class CallRecordSerializer(Serializer):
    """
    Serializer that gathers information from Call Start and Call End models.
    """
    start = DateTimeField()
    end = DateTimeField()
    call_id = CharField()
    destination = CharField()
    duration = DurationField()
    price = DecimalField(max_digits=10, decimal_places=2)
