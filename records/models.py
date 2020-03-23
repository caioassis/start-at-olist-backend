from django.core.validators import MaxLengthValidator, MinLengthValidator, RegexValidator
from django.db import models
from .querysets import CallRecordQuerySet


class CallRecord(models.Model):
    call_id = models.CharField(verbose_name='Call Unique ID', max_length=50, unique=True, help_text='Unique Call ID')
    timestamp = models.DateTimeField(verbose_name='Timestamp', help_text='Record Timestamp')

    class Meta:
        abstract = True


class CallStartRecord(CallRecord):
    source = models.CharField(verbose_name='Source', max_length=30, help_text='Source')
    destination = models.CharField(
        verbose_name='Destination',
        max_length=11,
        validators=[
            MinLengthValidator(10),
            MaxLengthValidator(11),
            RegexValidator(regex=r'^\d+$', message='Destination must contain only numbers.')
        ],
        help_text='Destination'
    )


class CallEndRecord(CallRecord):
    price = models.DecimalField(verbose_name='Price', decimal_places=2, max_digits=5, blank=True, null=True)

    objects = CallRecordQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=['timestamp'], name='idx_callendrecord_timestamp')
        ]
