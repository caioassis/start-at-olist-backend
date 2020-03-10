from typing import List
from django.db.models import Manager
from datetime import datetime


class CallRecordManager(Manager):

    def get_calls(self, from_date: datetime, to_date: datetime, **kwargs) -> List:
        return []
