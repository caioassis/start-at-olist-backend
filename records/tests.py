import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_DOWN
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.status import HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.test import APIClient, APITestCase
from .models import CallEndRecord, CallStartRecord


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


class CallStartRecordAPITestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        cls.post_url = reverse('call_start_record_create')

    def test_new_call_start_record(self):
        response = self.client.post(self.post_url)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        data = {
            'source': '505',
            'destination': '1234567890',
            'call_id': '12345'
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        record = response.data
        self.assertEqual(record['id'], 1)

    def test_new_call_start_record_requires_fields(self):
        required_fields = ['call_id', 'destination', 'source']
        response = self.client.post(self.post_url)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        response_required_fields = sorted(list(response.data.keys()))
        self.assertEqual(response_required_fields, required_fields)

    def test_new_call_start_record_with_duplicated_call_id(self):
        data = {
            'source': '505',
            'destination': '1234567890',
            'call_id': '12345'
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_new_call_start_record_with_destination(self):
        data = {
            'source': '505',
            'destination': '1a2b3c4d',  # invalid destination
            'call_id': str(uuid.uuid4())
        }
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        data['call_id'] = str(uuid.uuid4())
        data['destination'] = '1122334455'  # valid destination (length 10)
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        data['call_id'] = str(uuid.uuid4())
        data['destination'] = '11223344556'  # valid destination (length 11)
        response = self.client.post(self.post_url, data)
        self.assertEqual(response.status_code, HTTP_201_CREATED)


class CallEndRecordAPITestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        cls.post_url = reverse('call_end_record_create')
        cls.call_start_record = CallStartRecord.objects.create(source='505', call_id=str(uuid.uuid4()), destination='1234567890')

    def test_new_call_end_record(self):
        call_id = self.call_start_record.call_id
        timestamp = self.call_start_record.timestamp + timedelta(minutes=5)
        response = self.client.post(self.post_url, {'call_id': call_id, 'timestamp': timestamp})
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertIsNotNone(response.data['price'])
