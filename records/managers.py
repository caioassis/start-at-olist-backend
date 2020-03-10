from datetime import datetime
from typing import List
from django.db import connection
from django.db.models import Manager


class CallRecordManager(Manager):

    def get_calls(self, from_date: datetime, to_date: datetime, **kwargs) -> List:
        with connection.cursor() as cursor:
            # TO-DO
            # String formatting is insecure, so put query params in execute statement
            query = 'SELECT csr.call_id AS call_id, csr.timestamp AS start, cer.timestamp AS end, ' \
                    'csr.destination AS destination, CAST((julianday(cer.timestamp) - julianday(csr.timestamp)) * ' \
                    '24 * 60 * 60 AS real) AS duration, cer.price AS price FROM records_callstartrecord csr, ' \
                    'records_callendrecord cer WHERE csr.call_id=cer.call_id AND cer.timestamp BETWEEN "%s" ' \
                    'AND "%s"' % (from_date.strftime('%Y-%m-%d %H:%M:%S.%f'), to_date.strftime('%Y-%m-%d %H:%M:%S.%f'))
            query_conditions = ' AND '.join(['%s="%s"' % (k, v) for k, v in kwargs.items()])
            if query_conditions:
                query += ' AND '
                query += query_conditions
            cursor.execute(query)
            records = cursor.fetchall()
        fields = ['call_id', 'start', 'end', 'destination', 'duration', 'price']
        return list(map(lambda rec: dict(zip(fields, rec)), records))
