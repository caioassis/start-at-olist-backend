import uuid
from datetime import timedelta
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone
from records.models import CallEndRecord, CallStartRecord


class CallStartRecordTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.data = {
            'timestamp': timezone.now(),
            'call_id': str(uuid.uuid4()),
            'source': '99988526423',
            'destination': '9993468278'
        }

    def test_source_is_not_null(self):
        field = CallStartRecord._meta.get_field('source')
        self.assertFalse(field.null)

    def test_destination_is_not_null(self):
        field = CallStartRecord._meta.get_field('destination')
        self.assertFalse(field.null)

    def test_new_call_start_record(self):
        record = CallStartRecord.objects.create(**self.data)
        self.assertIsNotNone(record.pk)

    def test_new_call_start_record_without_timestamp(self):
        del self.data['timestamp']
        with self.assertRaises(IntegrityError):
            CallStartRecord.objects.create(**self.data)

    def test_new_call_start_record_with_empty_source(self):
        del self.data['source']
        record = CallStartRecord.objects.create(**self.data)
        self.assertEqual(record.source, '')

    def test_new_call_start_record_with_empty_destination(self):
        del self.data['destination']
        record = CallStartRecord.objects.create(**self.data)
        self.assertEqual(record.destination, '')

    def test_new_call_start_record_with_duplicated_call_id(self):
        with self.assertRaises(IntegrityError):
            CallStartRecord.objects.bulk_create([
                CallStartRecord(**self.data),
                CallStartRecord(**self.data)
            ])


class CallEndRecordTestCase(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.call_start_record = CallStartRecord.objects.create(**{
            'timestamp': timezone.now(),
            'call_id': str(uuid.uuid4()),
            'source': '99988526423',
            'destination': '9993468278'
        })

    def test_new_call_end_record(self):
        record = CallEndRecord.objects.create(
            call_id=self.call_start_record.call_id,
            timestamp=self.call_start_record.timestamp + timedelta(minutes=5)
        )
        self.assertIsNotNone(record.pk)
        self.assertIsNotNone(record.price)

    def test_new_call_end_record_without_timestamp(self):
        with self.assertRaises(IntegrityError):
            CallEndRecord.objects.create(call_id=self.call_start_record.call_id)

    def test_new_call_end_record_without_call_id(self):
        record = CallEndRecord.objects.create(
            timestamp=self.call_start_record.timestamp + timedelta(minutes=5)
        )
        self.assertEqual(record.call_id, '')

    def test_new_call_end_record_with_duplicated_call_id(self):
        with self.assertRaises(IntegrityError):
            CallEndRecord.objects.bulk_create([
                CallEndRecord(
                    call_id=self.call_start_record.call_id,
                    timestamp=self.call_start_record.timestamp + timedelta(minutes=5)
                ),
                CallEndRecord(
                    call_id=self.call_start_record.call_id,
                    timestamp=self.call_start_record.timestamp + timedelta(minutes=5)
                )
            ])
