import uuid
from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from freezegun import freeze_time
from rest_framework.exceptions import ErrorDetail
from records.serializers import CallEndRecordCreateSerializer, CallRecordSerializer, CallStartRecordSerializer
from records.utils import calculate_call_rate


@freeze_time('2020-01-01')
class CallStartRecordSerializerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = timezone.now()
        source = '9998852642'
        destination = '9993468278'
        cls.data = {
            'timestamp': today,
            'source': source,
            'destination': destination,
            'call_id': str(uuid.uuid4())
        }

    def test_serializer_is_valid(self):
        serializer = CallStartRecordSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        expected_fields = ['call_id', 'timestamp', 'source', 'destination']
        self.assertSetEqual(set(serializer.data.keys()), set(expected_fields))

    def test_serializer_creates_object(self):
        serializer = CallStartRecordSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(serializer.Meta.model.objects.count(), 1)

    def test_serializer_with_invalid_destination(self):
        data = self.data.copy()
        data['destination'] = data['destination'][:9]
        serializer = CallStartRecordSerializer(data=data)
        serializer.is_valid()
        self.assertIn('destination', serializer.errors)
        self.assertEqual(
            serializer.errors['destination'],
            [ErrorDetail(string='Ensure this field has at least 10 characters.', code='min_length')]
        )

    def test_serializer_without_required_fields(self):
        required_field_error = [ErrorDetail(string='This field is required.', code='required')]
        expected_serializer_errors = {
            'source': required_field_error,
            'destination': required_field_error,
            'timestamp': required_field_error,
            'call_id': required_field_error
        }
        for field in self.data.keys():
            with self.subTest(field=field):
                data = self.data.copy()
                del data[field]
                serializer = CallStartRecordSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertListEqual(serializer.errors[field], expected_serializer_errors[field])


@freeze_time('2020-01-01')
class CallEndRecordCreateSerializerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = timezone.now()
        source = '9998852642'
        destination = '9993468278'
        call_id = str(uuid.uuid4())
        cls.call_start_serializer = CallStartRecordSerializer(data={
            'timestamp': today,
            'source': source,
            'destination': destination,
            'call_id': call_id
        })
        cls.call_start_serializer.is_valid(raise_exception=True)
        cls.call_start_obj = cls.call_start_serializer.save()
        cls.data = {
            'timestamp': today + timedelta(minutes=5),
            'call_id': call_id
        }

    def test_serializer_is_valid(self):
        serializer = CallEndRecordCreateSerializer(data=self.data)
        serializer.is_valid(raise_exception=False)
        expected_fields = ['call_id', 'timestamp']
        self.assertSetEqual(set(serializer.data.keys()), set(expected_fields))

    def test_serializer_creates_object(self):
        serializer = CallEndRecordCreateSerializer(data=self.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        self.assertEqual(serializer.Meta.model.objects.count(), 1)

    def test_serializer_without_required_fields(self):
        required_field_error = [ErrorDetail(string='This field is required.', code='required')]
        expected_serializer_errors = {
            'timestamp': required_field_error,
            'call_id': required_field_error
        }
        for field in self.data.keys():
            with self.subTest(field=field):
                data = self.data.copy()
                del data[field]
                serializer = CallEndRecordCreateSerializer(data=data)
                self.assertFalse(serializer.is_valid())
                self.assertListEqual(serializer.errors[field], expected_serializer_errors[field])

    def test_serializer_with_invalid_timestamp(self):
        data = self.data.copy()
        data['timestamp'] = self.call_start_obj.timestamp - timedelta(minutes=5)
        serializer = CallEndRecordCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertListEqual(
            serializer.errors['non_field_errors'],
            [ErrorDetail(string='Call end record timestamp cannot be earlier than call start record timestamp.', code='invalid')]
        )

    def test_serializer_with_inexistent_call_id(self):
        data = self.data.copy()
        data['call_id'] = '123'
        serializer = CallEndRecordCreateSerializer(data=data)
        self.assertFalse(serializer.is_valid())
        self.assertListEqual(
            serializer.errors['non_field_errors'],
            [ErrorDetail(string='Given call_id does not exist.', code='invalid')]
        )


@freeze_time('2020-01-01')
class CallRecordSerializerTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        today = timezone.now()
        start = today
        end = today + timedelta(minutes=5)
        source = '9998852642'
        destination = '9993468278'
        call_id = str(uuid.uuid4())
        price = calculate_call_rate(start, end)
        duration = end - start
        cls.data = {
            'start': start,
            'end': end,
            'source': source,
            'destination': destination,
            'call_id': call_id,
            'price': price,
            'duration': duration
        }

    def test_serializer_is_valid(self):
        serializer = CallRecordSerializer(data=self.data)
        self.assertTrue(serializer.is_valid())
        print(serializer.data)  # This raises an KeyError
