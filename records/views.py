import re
from datetime import timedelta
from django.utils import timezone
from rest_framework.generics import CreateAPIView
from rest_framework.response import Response
from rest_framework.status import HTTP_400_BAD_REQUEST
from rest_framework.views import APIView
from .serializers import CallStartRecordSerializer, CallEndRecordCreateSerializer, CallRecordSerializer
from .models import CallEndRecord


class CallStartRecordAPIView(CreateAPIView):
    serializer_class = CallStartRecordSerializer


class CallEndRecordAPIView(CreateAPIView):
    serializer_class = CallEndRecordCreateSerializer


class TelephonyBillAPIView(APIView):

    def get(self, request, *args, **kwargs):
        source = request.query_params.get('source', None)
        if not source:
            return Response({'source': 'This field is required.'}, status=HTTP_400_BAD_REQUEST)
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        period = request.query_params.get('period', None)
        if period:
            if not re.match(r'^\d{4}-\d{2}$', period):
                return Response({'period': 'Period must be in YYYY-MM format.'}, status=HTTP_400_BAD_REQUEST)
            year, month = tuple(map(lambda v: int(v), period.split('-')))
            if (not 1900 <= year <= today.year) or (not 1 <= month <= 12):
                return Response({'period': 'Period is invalid.'}, status=HTTP_400_BAD_REQUEST)
            if today.year == year:
                if today.month == month:
                    return Response({'invalid': 'You can\'t get bills from current month.'}, status=HTTP_400_BAD_REQUEST)
                elif today.month < month:
                    return Response({'invalid': 'You can\'t get bills from next months.'}, status=HTTP_400_BAD_REQUEST)
            from_date = today.replace(year=year, month=month, day=1)
            to_date = from_date
            while to_date.month == from_date.month:
                to_date += timedelta(days=1)
        else:
            current_month = today.replace(day=1)
            last_month = (current_month - timedelta(days=1)).replace(day=1)
            from_date = last_month
            to_date = current_month
        records = CallEndRecord.objects.get_calls(from_date, to_date, source=source)
        serializer = CallRecordSerializer(records, many=True)
        return Response({'source': source, 'start_period': from_date, 'end_period': to_date, 'records': serializer.data})
