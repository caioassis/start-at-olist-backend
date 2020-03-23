import random
import uuid
from datetime import timedelta
from django.urls import reverse
from django.utils import dateparse, timezone
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST
from rest_framework.test import APIClient, APITestCase
from records.models import CallEndRecord, CallStartRecord


class CallStartRecordAPITestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        cls.post_url = reverse('call_start_record_create')
        cls.today = timezone.now().strftime('%Y-%m-%dT%H:%M:%S%z')

    def test_new_call_start_record(self):
        response = self.client.post(self.post_url, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        data = {
            'source': '505',
            'destination': '1234567890',
            'call_id': '12345',
            'timestamp': self.today
        }
        response = self.client.post(self.post_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertEqual(CallStartRecord.objects.all().count(), 1)

    def test_new_call_start_record_requires_fields(self):
        required_fields = ['call_id', 'destination', 'source', 'timestamp']
        response = self.client.post(self.post_url, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        response_required_fields = sorted(list(response.data.keys()))
        self.assertEqual(response_required_fields, required_fields)

    def test_new_call_start_record_with_duplicated_call_id(self):
        data = {
            'source': '505',
            'destination': '1234567890',
            'call_id': '12345',
            'timestamp': self.today
        }
        response = self.client.post(self.post_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        response = self.client.post(self.post_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_new_call_start_record_with_destination(self):
        data = {
            'source': '505',
            'destination': '1a2b3c4d',  # invalid destination
            'call_id': str(uuid.uuid4()),
            'timestamp': self.today
        }
        response = self.client.post(self.post_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        data['call_id'] = str(uuid.uuid4())
        data['destination'] = '1122334455'  # valid destination (length 10)
        response = self.client.post(self.post_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        data['call_id'] = str(uuid.uuid4())
        data['destination'] = '11223344556'  # valid destination (length 11)
        response = self.client.post(self.post_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)


class CallEndRecordAPITestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        today = timezone.now()
        cls.client = APIClient()
        cls.post_url = reverse('call_end_record_create')
        cls.call_start_record = CallStartRecord.objects.create(source='505', call_id=str(uuid.uuid4()),
                                                               destination='1234567890', timestamp=today)

    def test_new_call_end_record(self):
        call_id = self.call_start_record.call_id
        timestamp = self.call_start_record.timestamp + timedelta(minutes=5)
        response = self.client.post(self.post_url, {'call_id': call_id, 'timestamp': timestamp}, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertIn('timestamp', response.data)
        call_end_record_timestamp = dateparse.parse_datetime(response.data['timestamp'])
        self.assertEqual(call_end_record_timestamp, timestamp)
        self.assertIsNotNone(response.data['price'])


class TelephonyBillAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        today = timezone.now().replace(hour=0, minute=0, second=0, microsecond=0)
        last_month = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        cls.source = '505'
        destination = ''.join([str(random.randint(1, 9)) for i in range(random.randint(10, 11))])

        # Record that started in the last day of month and ended in the first day of next month
        call_id = str(uuid.uuid4())
        cls.intermonths_billable_record = (
            CallStartRecord.objects.create(call_id=call_id, source=cls.source, destination=destination,
                                           timestamp=today.replace(day=1, hour=5) - timedelta(days=1)),
            CallEndRecord.objects.create(call_id=call_id, timestamp=today.replace(day=1, hour=5, minute=5))
        )

        # Record that has price of 0
        call_id = str(uuid.uuid4())
        cls.free_of_charge_record = (
            CallStartRecord.objects.create(call_id=call_id, source=cls.source, destination=destination,
                                           timestamp=last_month.replace(hour=5)),
            CallEndRecord.objects.create(call_id=call_id, timestamp=last_month.replace(hour=5, minute=5))
        )

        # Record that is priced
        call_id = str(uuid.uuid4())
        cls.billable_record = (
            CallStartRecord.objects.create(call_id=call_id, source=cls.source, destination=destination,
                                           timestamp=last_month.replace(hour=6)),
            CallEndRecord.objects.create(call_id=call_id, timestamp=last_month.replace(hour=6, minute=5))
        )

        # Record whose call started one day and ended the other, but it has price of 0
        call_id = str(uuid.uuid4())
        cls.interdays_unbillable_record = (
            CallStartRecord.objects.create(call_id=call_id, source=cls.source, destination=destination,
                                           timestamp=last_month.replace(hour=22)),
            CallEndRecord.objects.create(call_id=call_id,
                                         timestamp=(last_month + timedelta(days=1)).replace(hour=5, minute=55))
        )

        # Record whose call started one thay and ended another day, but it is priced
        call_id = str(uuid.uuid4())
        cls.interdays_billable_record = (
            CallStartRecord.objects.create(call_id=call_id, source=cls.source, destination=destination,
                                           timestamp=last_month.replace(hour=6)),
            CallEndRecord.objects.create(call_id=call_id, timestamp=(last_month + timedelta(days=2)).replace(hour=22))
        )

        # Random record of same source from current month
        call_id = str(uuid.uuid4())
        CallStartRecord.objects.create(call_id=call_id, timestamp=today, source=cls.source, destination=destination)
        CallEndRecord.objects.create(call_id=call_id, timestamp=today + timedelta(seconds=60))

        # Random records to populate database and make it possible to check for correct bill results
        for _ in range(10):
            call_id = str(uuid.uuid4())
            timestamp = today - timedelta(days=random.randint(1, 90), hours=random.randint(0, 5),
                                          minutes=random.randint(0, 59))
            source = '123'
            destination = ''.join([str(random.randint(1, 9)) for i in range(random.randint(10, 11))])
            CallStartRecord.objects.create(call_id=call_id, timestamp=timestamp, source=source, destination=destination)
            CallEndRecord.objects.create(call_id=call_id, timestamp=timestamp + timedelta(seconds=random.randint(0, 9000)))

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        cls.url = '/v1/call-records/bills/'

    def test_retrieve_telephony_bill(self):
        response = self.client.get(self.url, {'source': self.source})
        self.assertEqual(response.status_code, HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 4)
        current_month = timezone.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month = (current_month - timedelta(days=1)).replace(day=1)
        self.assertEqual(response.data['start_period'], last_month)
        self.assertEqual(response.data['end_period'], current_month)

    def test_retrieve_telephony_bill_of_this_month(self):
        today = timezone.now().date().strftime('%Y-%m')
        response = self.client.get(self.url, {'period': today, 'source': self.source})
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)

    def test_retrieve_telephony_bill_of_next_month(self):
        today = timezone.now()
        date = timezone.now()
        while today.month == date.month:
            date += timedelta(days=1)
        date = date.strftime('%Y-%m')
        response = self.client.get(self.url, {'period': date, 'source': self.source})
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertIn('invalid', response.data)

    def test_retrieve_telephony_bill_without_source(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        self.assertIn('source', response.data)