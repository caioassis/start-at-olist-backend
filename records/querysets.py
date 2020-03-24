from datetime import datetime
from django.apps import apps
from django.db.models import DateTimeField, DurationField, ExpressionWrapper, F, OuterRef, QuerySet, Subquery
from django.db.models.functions import Cast
from .exceptions import InvalidDatePeriodException


class CallRecordQuerySet(QuerySet):

    def get_calls(self, from_date: datetime, to_date: datetime, source=None) -> QuerySet:
        if not isinstance(from_date, datetime) or not isinstance(to_date, datetime):
            raise TypeError('Params from_date and to_date must be a datetime object.')
        if from_date > to_date:
            raise InvalidDatePeriodException('Starting date cannot be higher than ending date.')
        CallStartRecord = apps.get_model('records', 'CallStartRecord')
        CallEndRecord = apps.get_model('records', 'CallEndRecord')
        call_start_records = CallStartRecord.objects.filter(call_id=OuterRef('call_id'))
        records = CallEndRecord.objects.filter(timestamp__range=(from_date, to_date))
        records = records.annotate(
            start=Subquery(call_start_records.values('timestamp')),
            end=F('timestamp'),
            source=Subquery(call_start_records.values('source')),
            destination=Subquery(call_start_records.values('destination')),
            duration=ExpressionWrapper(
                Cast('end', output_field=DateTimeField()) - Cast('start', output_field=DateTimeField()),
                output_field=DurationField()
            )
        )
        if source:
            records = records.filter(source=source)
        records = records.order_by('end').values('start', 'end', 'call_id', 'source', 'destination', 'duration', 'price')
        return records
