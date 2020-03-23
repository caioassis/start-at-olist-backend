from django.db.models.signals import pre_save
from django.dispatch import receiver
from .models import CallEndRecord, CallStartRecord
from .utils import calculate_call_rate


@receiver(pre_save, sender=CallEndRecord)
def save_price(sender, instance, **kwargs):
    try:
        call_start = CallStartRecord.objects.get(call_id=instance.call_id)
    except CallStartRecord.DoesNotExist:
        pass
    else:
        instance.price = calculate_call_rate(call_start.timestamp, instance.timestamp)
