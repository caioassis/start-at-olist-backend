from django.core.validators import MaxLengthValidator, MinLengthValidator, RegexValidator
from django.db import models
from .querysets import CallRecordQuerySet
from .utils import calculate_call_rate


class CallRecord(models.Model):
    call_id = models.CharField(verbose_name='Call Unique ID', max_length=50, unique=True)
    timestamp = models.DateTimeField(verbose_name='Timestamp')

    class Meta:
        abstract = True


class CallStartRecord(CallRecord):
    source = models.CharField(verbose_name='Source', max_length=30)
    destination = models.CharField(
        verbose_name='Destination',
        max_length=11,
        validators=[
            MinLengthValidator(10),
            MaxLengthValidator(11),
            RegexValidator(regex=r'^\d+$', message='Destination must contain only numbers.')
        ]
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['call_id'], name='callstartrecord_unique_callid')
        ]


class CallEndRecord(CallRecord):
    price = models.DecimalField(verbose_name='Price', decimal_places=2, max_digits=5, blank=True, null=True)

    objects = CallRecordQuerySet.as_manager()

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['call_id'], name='callendrecord_unique_callid')
        ]
