from rest_framework.fields import Field
from datetime import timedelta


class DurationField(Field):
    """
    Field that represents duration in ' h m s' format.
    """

    def to_representation(self, value: timedelta):
        duration = int(value.total_seconds())
        hours, duration = divmod(duration, 60 * 60)
        minutes, duration = divmod(duration, 60)
        seconds = duration
        return f'{hours}h{minutes}m{seconds}s'

    def to_internal_value(self, value):
        return value
