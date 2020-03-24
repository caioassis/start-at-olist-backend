import random
import uuid
from datetime import timedelta
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.status import HTTP_200_OK, HTTP_201_CREATED, HTTP_400_BAD_REQUEST, HTTP_422_UNPROCESSABLE_ENTITY
from rest_framework.test import APIClient, APITestCase
from records.models import CallEndRecord, CallStartRecord


@freeze_time('2020-02-01')
class CallStartRecordAPITestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        cls.post_url = reverse('call_start_record_create')
        cls.data = {
            'source': '9998852642',
            'destination': '9993468278',
            'call_id': str(uuid.uuid4()),
            'timestamp': timezone.now()
        }

    def test_create_call_start_record(self):
        response = self.client.post(self.post_url, self.data, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertEqual(CallStartRecord.objects.all().count(), 1)
        expected_fields = ['id', 'source', 'destination', 'timestamp', 'call_id']
        self.assertSetEqual(set(response.data.keys()), set(expected_fields))

    def test_new_call_start_record_requires_fields(self):
        required_field_error = ['This field is required.']
        expected_errors = {
            'source': required_field_error,
            'destination': required_field_error,
            'timestamp': required_field_error,
            'call_id': required_field_error
        }
        for field in self.data.keys():
            with self.subTest(field=field):
                data = self.data.copy()
                del data[field]
                response = self.client.post(self.post_url, data, format='json')
                self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
                self.assertListEqual(response.data[field], expected_errors[field])

    def test_new_call_start_record_with_duplicated_call_id(self):
        CallStartRecord.objects.create(**self.data)
        response = self.client.post(self.post_url, self.data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        content = response.json()
        self.assertDictEqual(
            content,
            {'call_id': ['call start record with this Call Unique ID already exists.']}
        )

    def test_new_call_start_record_with_invalid_destination(self):
        data = self.data.copy()
        invalid_destinations = [
            '123456789',  # length 9
            '123456789012'  # length 12
        ]

        data['destination'] = invalid_destinations.pop(0)
        response = self.client.post(self.post_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        content = response.json()
        self.assertDictEqual(content, {'destination': ['Ensure this field has at least 10 characters.']})

        data['destination'] = invalid_destinations.pop(0)
        response = self.client.post(self.post_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        content = response.json()
        self.assertDictEqual(content, {'destination': ['Ensure this field has no more than 11 characters.']})


@freeze_time('2020-02-01')
class CallEndRecordAPITestCase(APITestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.client = APIClient()
        cls.post_url = reverse('call_end_record_create')
        cls.call_start_record = CallStartRecord.objects.create(**{
            'source': '9998852642',
            'destination': '9993468278',
            'call_id': str(uuid.uuid4()),
            'timestamp': timezone.now()
        })

    def test_create_call_end_record(self):
        call_id = self.call_start_record.call_id
        timestamp = self.call_start_record.timestamp + timedelta(minutes=5)
        response = self.client.post(self.post_url, {'call_id': call_id, 'timestamp': timestamp}, format='json')
        self.assertEqual(response.status_code, HTTP_201_CREATED)
        self.assertEqual(CallEndRecord.objects.count(), 1)
        content = response.json()
        expected_fields = ['id', 'timestamp', 'call_id', 'price']
        self.assertSetEqual(set(content.keys()), set(expected_fields))

    def test_create_call_end_record_requires_fields(self):
        required_field_error = ['This field is required.']
        expected_errors = {
            'timestamp': required_field_error,
            'call_id': required_field_error
        }
        data = {
            'call_id': self.call_start_record.call_id,
            'timestamp': self.call_start_record.timestamp + timedelta(minutes=5)
        }
        for field in data.keys():
            with self.subTest(field=field):
                payload = data.copy()
                del payload[field]
                response = self.client.post(self.post_url, payload, format='json')
                self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
                content = response.json()
                self.assertListEqual(content[field], expected_errors[field])

    def test_create_call_end_record_with_inexistent_call_id(self):
        inexistent_call_id = str(uuid.uuid4())
        data = {
            'call_id': inexistent_call_id,
            'timestamp': self.call_start_record.timestamp + timedelta(minutes=5)
        }
        response = self.client.post(self.post_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        content = response.json()
        self.assertDictEqual(content, {'call_id': ['Given call_id does not exist.']})

    def test_create_call_end_record_with_invalid_timestamp(self):
        invalid_timestamp = self.call_start_record.timestamp - timedelta(minutes=5)
        data = {
            'call_id': self.call_start_record.call_id,
            'timestamp': invalid_timestamp
        }
        response = self.client.post(self.post_url, data, format='json')
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        content = response.json()
        self.assertDictEqual(
            content,
            {'timestamp': ['Call end record timestamp cannot be earlier than call start record timestamp.']}
        )


@freeze_time('2020-02-01')
class TelephonyBillAPITestCase(APITestCase):

    @classmethod
    def setUpTestData(cls):
        today = timezone.now()
        last_month = (today - timedelta(days=1)).replace(day=1)
        cls.source = '9998852642'
        destination = '9993468278'

        # Record that started in the last day of month and ended in the first day of next month
        call_id = str(uuid.uuid4())
        cls.intermonths_billable_record = (
            CallStartRecord.objects.create(call_id=call_id, source=cls.source, destination=destination,
                                           timestamp=today.replace(hour=5) - timedelta(days=1)),
            CallEndRecord.objects.create(call_id=call_id, timestamp=today.replace(hour=5, minute=5))
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

        # Record whose call started one day and ended another day, but it is priced
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
        content = response.json()
        self.assertIn('results', content)
        self.assertEqual(len(content['results']), 4)
        start_period = '2020-01-01T00:00:00Z'
        end_period = '2020-02-01T00:00:00Z'
        self.assertEqual(content['start_period'], start_period)
        self.assertEqual(content['end_period'], end_period)

    def test_retrieve_telephony_bill_of_this_month(self):
        today = timezone.now().date().strftime('%Y-%m')
        response = self.client.get(self.url, {'period': today, 'source': self.source})
        self.assertEqual(response.status_code, HTTP_422_UNPROCESSABLE_ENTITY)
        content = response.json()
        self.assertDictEqual(
            content,
            {'period': "You can't get bills from current month."}
        )

    def test_retrieve_telephony_bill_of_next_month(self):
        next_month = '2020-03'
        response = self.client.get(self.url, {'period': next_month, 'source': self.source})
        self.assertEqual(response.status_code, HTTP_422_UNPROCESSABLE_ENTITY)
        content = response.json()
        self.assertDictEqual(
            content,
            {'period': "You can't get bills from next months."}
        )

    def test_retrieve_telephony_bill_without_source(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, HTTP_400_BAD_REQUEST)
        content = response.json()
        self.assertDictEqual(content, {'source': 'This field is required.'})
