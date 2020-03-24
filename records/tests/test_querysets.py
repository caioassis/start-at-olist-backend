import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from records.exceptions import InvalidDatePeriodException
from records.models import CallEndRecord, CallStartRecord


@freeze_time('2020-01-01')
class CallRecordQuerySetTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.source = '99988526423'
        cls.destination = '9993468278'
        today = timezone.now().replace(hour=12)
        yesterday = today - timedelta(days=1)

        # Call started and ended yesterday
        call_id = str(uuid.uuid4())
        CallStartRecord.objects.create(call_id=call_id, timestamp=yesterday, source=cls.source, destination=cls.destination)
        CallEndRecord.objects.create(call_id=call_id, timestamp=yesterday + timedelta(minutes=5))

        # Call started yesterday and ended today
        call_id = str(uuid.uuid4())
        CallStartRecord.objects.create(call_id=call_id, timestamp=yesterday, source=cls.source, destination=cls.destination)
        CallEndRecord.objects.create(call_id=call_id, timestamp=today)

        # Call started and ended today
        call_id = str(uuid.uuid4())
        CallStartRecord.objects.create(call_id=call_id, timestamp=today, source=cls.source, destination=cls.destination)
        CallEndRecord.objects.create(call_id=call_id, timestamp=today + timedelta(minutes=5))

        # Call with different source, not to be retrived by get_calls method.
        call_id = str(uuid.uuid4())
        CallStartRecord.objects.create(call_id=call_id, timestamp=today, source='1234567890', destination=cls.destination)
        CallEndRecord.objects.create(call_id=call_id, timestamp=today + timedelta(minutes=5))

    def test_get_calls(self):
        today = timezone.now()
        from_date = today.replace(hour=0)
        to_date = today.replace(hour=23, minute=59, second=59, microsecond=59)
        queryset = CallEndRecord.objects.get_calls(from_date, to_date)
        self.assertEqual(queryset.count(), 3)

    def test_get_calls_with_source(self):
        today = timezone.now()
        from_date = today.replace(hour=0)
        to_date = today.replace(hour=23, minute=59, second=59, microsecond=59)
        queryset = CallEndRecord.objects.get_calls(from_date, to_date, source=self.source)
        self.assertEqual(queryset.count(), 2)
        self.assertSetEqual(set(queryset.values_list('source', flat=True)), {self.source})

    def test_get_calls_with_inexistent_source(self):
        today = timezone.now()
        from_date = today.replace(hour=0)
        to_date = today.replace(hour=23, minute=59, second=59, microsecond=59)
        queryset = CallEndRecord.objects.get_calls(from_date, to_date, source='123')
        self.assertFalse(queryset.exists())

    def test_get_calls_with_invalid_date_inputs(self):
        from_date = timezone.now()
        to_date = from_date - timedelta(days=1)
        with self.assertRaises(InvalidDatePeriodException):
            CallEndRecord.objects.get_calls(from_date, to_date)

    def test_get_calls_with_incorrect_input_types(self):
        cases = [
            (str('1'), str('1')),
            (int(1), int(1)),
            (float(1), float(1))
        ]
        for index, case in enumerate(cases):
            with self.subTest(index=index):
                with self.assertRaises(TypeError):
                    CallEndRecord.objects.get_calls(*case)
