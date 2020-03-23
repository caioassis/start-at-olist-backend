from datetime import datetime, timedelta
from decimal import Decimal
from django.conf import settings

MINUTE_RATE = settings.MINUTE_RATE
CONNECTION_FEE = settings.CONNECTION_FEE


def calculate_call_rate(call_start: datetime, call_end: datetime) -> Decimal:
    minute_rate = 0
    billable_minutes = 0
    call_seconds = 0
    # Check if call started one day and ended the other
    if call_start.date() != call_end.date():
        # Check how many full days between call started and ended
        full_days = 0
        while (call_start.date() + timedelta(days=full_days)) != (call_end.date() - timedelta(days=1)):
            full_days += 1
        if full_days:
            call_seconds += full_days * 16 * 60 * 60  # Consider one full day of talk

        # Calculate how many seconds were talked on call starting day
        start_date = call_start.replace(hour=6, minute=0, second=0, microsecond=0)
        end_date = call_start.replace(hour=22, minute=0, second=0, microsecond=0)
        if call_start < start_date:
            call_start = start_date
        if call_start < end_date:
            call_seconds += int((end_date - call_start).total_seconds())

        # Calculate how many seconds were talked on call ending day
        start_date = call_end.replace(hour=6, minute=0, second=0, microsecond=0)
        end_date = call_end.replace(hour=22, minute=0, second=0, microsecond=0)
        if call_end > end_date:
            call_end = end_date
        if call_end >= start_date:
            call_seconds += int((call_end - start_date).total_seconds())
    else:
        start_date = call_end.replace(hour=6, minute=0, second=0, microsecond=0)
        end_date = call_end.replace(hour=22, minute=0, second=0, microsecond=0)
        if call_start < start_date:
            call_start = call_start.replace(hour=6, minute=0, second=0, microsecond=0)
        if call_end > end_date:
            call_end = call_end.replace(hour=22, minute=0, second=0, microsecond=0)
        call_seconds += int((call_end - call_start).total_seconds())

    billable_minutes += call_seconds // 60
    if billable_minutes > 0:
        minute_rate = MINUTE_RATE
    cost = CONNECTION_FEE + (minute_rate * billable_minutes)
    # Round cost to 2 decimal places
    cost = str(round(cost, 2))
    return Decimal(cost)
