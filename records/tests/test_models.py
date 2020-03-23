import uuid
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from records.models import CallEndRecord, CallStartRecord
from records.utils import calculate_call_rate


class CallStartRecordTestCase(TestCase):

    def test_new_call_record_has_timestamp(self):
        today = timezone.now()
        rec = CallStartRecord.objects.create(call_id=uuid.uuid4(), source='505', destination='1234567890', timestamp=today)
        self.assertIsInstance(rec.timestamp, datetime)


class CallEndRecordTestCase(TestCase):

    def test_new_call_record_has_price(self):
        today = timezone.now().replace(hour=6, minute=0, second=0, microsecond=0)
        start_rec = CallStartRecord.objects.create(call_id=uuid.uuid4(), source='505', destination='1234567890', timestamp=today)
        end_rec = CallEndRecord.objects.create(call_id=start_rec.call_id, timestamp=today + timedelta(minutes=5))
        self.assertIsNotNone(end_rec.price)
        self.assertEqual(end_rec.price, calculate_call_rate(start_rec.timestamp, end_rec.timestamp))
