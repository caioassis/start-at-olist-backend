from datetime import datetime
from decimal import Decimal

MINUTE_RATE = 0.09
CONNECTION_FEE = 0.36


def calculate_call_rate(call_start: datetime, call_end: datetime) -> Decimal:
    minute_rate = 0
    billable_minutes = 0
    call_seconds = 0
    # check if call started one day and ended the other
    if call_start.date() != call_end.date():
        for date in [call_start, call_end]:
            start_date = date.replace(hour=6, minute=0, second=0, microsecond=0)
            end_date = date.replace(hour=22, minute=0, second=0, microsecond=0)
            if date < start_date:
                return Decimal(float(0))
            if date > end_date:
                date = date.replace(hour=22, minute=0, second=0, microsecond=0)
            call_seconds += int((date - start_date).total_seconds())
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
