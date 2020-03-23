from datetime import datetime
from django.test import TestCase
from records.utils import CONNECTION_FEE, MINUTE_RATE, calculate_call_rate


class CalculateCallRateTestCase(TestCase):

    def test_calculate_call_rate(self):
        cases = [
            {
                'start': datetime(2020, 3, 9, 12, 0, 0, 0),
                'end': datetime(2020, 3, 9, 13, 0, 0, 0),
                'billable_minutes': 60
            },
            {
                'start': datetime(2020, 3, 9, 5, 0, 0, 0),
                'end': datetime(2020, 3, 9, 5, 30, 0, 0),
                'billable_minutes': 0
            },
            {
                'start': datetime(2020, 3, 9, 22, 30, 0, 0),
                'end': datetime(2020, 3, 9, 23, 0, 0, 0),
                'billable_minutes': 0
            },
            {
                'start': datetime(2020, 3, 9, 5, 50, 0, 0),
                'end': datetime(2020, 3, 9, 6, 10, 0, 0),
                'billable_minutes': 10
            },
            {
                'start': datetime(2020, 3, 9, 21, 50, 0, 0),
                'end': datetime(2020, 3, 9, 22, 10, 0, 0),
                'billable_minutes': 10
            },
            {
                'start': datetime(2020, 3, 9, 5, 30, 0, 0),
                'end': datetime(2020, 3, 9, 22, 30, 0, 0),
                'billable_minutes': 960
            },
            {
                'start': datetime(2020, 3, 9, 12, 0, 0, 0),
                'end': datetime(2020, 3, 11, 12, 0, 0, 0),
                'billable_minutes': 1920
            }
        ]

        for index, case in enumerate(cases):
            with self.subTest(index=index):
                self.assertEqual(
                    float(calculate_call_rate(case['start'], case['end'])),
                    round((CONNECTION_FEE + MINUTE_RATE * case['billable_minutes']), 2)
                )