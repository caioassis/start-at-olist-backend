from datetime import datetime
from typing import List
from django.apps import apps
from django.db.models import DateTimeField, ExpressionWrapper, F, IntegerField, OuterRef, QuerySet, Subquery
from django.db.models.functions import Cast


class CallRecordQuerySet(QuerySet):

    def get_calls(self, from_date: datetime, to_date: datetime, **kwargs) -> List:
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
                ExpressionWrapper(
                    Cast('end', output_field=DateTimeField()) - Cast('start', output_field=DateTimeField()),
                    output_field=IntegerField()
                ) / 1_000_000,
                output_field=IntegerField()
            )
        )
        if kwargs:
            records = records.filter(**kwargs)
        records = records.order_by('end').values('start', 'end', 'call_id', 'source', 'destination', 'duration', 'price')
        return records
