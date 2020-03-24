import calendar
from datetime import datetime, timedelta
from django.utils import timezone
from rest_framework.exceptions import ValidationError
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet
from .exceptions import UnprocessableEntityError
from .models import CallEndRecord
from .pagination import TelephonyBillPagination
from .serializers import CallEndRecordCreateSerializer, CallRecordSerializer, CallStartRecordSerializer


class CallStartRecordAPIView(CreateAPIView):
    serializer_class = CallStartRecordSerializer


class CallEndRecordAPIView(CreateAPIView):
    serializer_class = CallEndRecordCreateSerializer


class TelephonyBillViewSet(GenericViewSet):
    pagination_class = TelephonyBillPagination
    serializer_class = CallRecordSerializer

    def get_queryset(self):
        source = self.request.query_params.get('source')
        period = self.request.query_params.get('period', None)
        period = self._clean_period(period)
        from_date, to_date = self._get_search_period(period)
        queryset = CallEndRecord.objects.get_calls(from_date, to_date, source=source)
        return queryset

    def _clean_period(self, period=None):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        if period:
            try:
                period = datetime.strptime(period, '%Y-%m')
            except ValueError:
                raise ValidationError({'period': 'Period is invalid. Must be in YYYY-MM format.'})

            same_year = today.year == period.year
            same_month = today.month == period.month
            if same_year and same_month:
                raise UnprocessableEntityError({'period': "You can't get bills from current month."})
            elif same_year and today.month < period.month:
                raise UnprocessableEntityError({'period': "You can't get bills from next months."})
        else:
            period = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        return period

    def _get_search_period(self, period: datetime) -> tuple:
        start = period
        _, last_day_of_month = calendar.monthrange(period.year, period.month)
        end = start.replace(day=last_day_of_month) + timedelta(days=1)
        return start, end

    def list(self, request, *args, **kwargs):
        source = self.request.query_params.get('source', None)
        if not source:
            raise ValidationError({'source': 'This field is required.'})
        period = self.request.query_params.get('period', None)
        period = self._clean_period(period)
        from_date, to_date = self._get_search_period(period)
        queryset = self.get_queryset()
        page = self.paginate_queryset(queryset)
        data = None
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            r = self.get_paginated_response(serializer.data)
            data = r.data
        else:
            serializer = self.get_serializer(queryset, many=True)
            data = serializer.data
        return Response({
            'source': source,
            'start_period': from_date,
            'end_period': to_date,
            **data
        })
