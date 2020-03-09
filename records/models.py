from django.db import models
from django.core.validators import RegexValidator, MinLengthValidator, MaxLengthValidator
from django.utils import timezone
from .utils import calculate_call_rate


class CallRecord(models.Model):
    call_id = models.CharField(verbose_name='Call Unique ID', max_length=50)
    timestamp = models.DateTimeField(verbose_name='Timestamp', blank=True)

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

    objects = models.Manager()

    def save(self, *args, **kwargs):
        if not self.timestamp:
            self.timestamp = timezone.now()
        super().save(*args, **kwargs)

    def __str__(self):
        return self.timestamp

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['call_id'], name='callstartrecord_unique_callid')
        ]


class CallEndRecord(CallRecord):
    price = models.DecimalField(verbose_name='Price', decimal_places=2, max_digits=5, blank=True, null=True)

    objects = models.Manager()

    def save(self, *args, **kwargs):
        if not self.timestamp:
            self.timestamp = timezone.now()
        if self.price is None:
            try:
                call_start = CallStartRecord.objects.get(call_id=self.call_id)
            except CallStartRecord.DoesNotExist:
                pass
            else:
                self.price = calculate_call_rate(call_start.timestamp, self.timestamp)
        super().save(*args, **kwargs)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['call_id'], name='callendrecord_unique_callid')
        ]
