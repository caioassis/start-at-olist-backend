import uuid
from decimal import Decimal, ROUND_DOWN
from datetime import datetime, timedelta
from django.test import TestCase
from django.utils import timezone
from .models import CallStartRecord, CallEndRecord


class CallStartRecordTestCase(TestCase):

    def test_new_call_record_has_timestamp(self):
        rec = CallStartRecord.objects.create(call_id=uuid.uuid4(), source='505', destination='1234567890')
        self.assertIsInstance(rec.timestamp, datetime)


class CallEndRecordTestCase(TestCase):

    def test_new_call_record_has_price(self):
        start_rec = CallStartRecord.objects.create(call_id=uuid.uuid4(), source='505', destination='1234567890')
        end_rec = CallEndRecord.objects.create(call_id=start_rec.call_id, timestamp=timezone.now() + timedelta(minutes=5))
        self.assertIsNotNone(end_rec.price)
        self.assertEqual(end_rec.price, Decimal(0.81).quantize(Decimal('.81'), rounding=ROUND_DOWN))
