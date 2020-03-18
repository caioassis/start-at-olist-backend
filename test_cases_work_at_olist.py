import pdb
import requests
import calendar
from datetime import datetime

URL = 'http://127.0.0.1:8000'
# URL = 'https://telecom-project-olist.herokuapp.com'
URL_START = f'{URL}/call_records/started/'
URL_END = f'{URL}/call_records/finished/'
URL_PRICE = ''

HEADERS = {
    'Content-Type': 'application/json;charset=UTF-8',
}

# tests from:
# https://jira-olist.atlassian.net/wiki/spaces/TECH/pages/162529315/Processo+de+Corre+o+do+Desafio

payloads = (
    (
        {
            'type': 'start',
            'timestamp': '2016-02-29T12:00:00Z',
            'call_id': 70,
            'source': '99988526423',
            'destination': '9993468278',
        },
        {
            'type': 'end',
            'timestamp': '2016-02-29T14:00:00Z',
            'call_id': 70,
        }
    ),
    (
        {
            'type': 'start',
            'timestamp': '2017-12-11T15:07:13Z',
            'call_id': 71,
            'source': '99988526423',
            'destination': '9993468278',
        },
        {
            'type': 'end',
            'timestamp': '2017-12-11T15:14:56Z',
            'call_id': 71,
        }
    ),
    (
        {
            'type': 'start',
            'timestamp': '2017-12-12T22:47:56Z',
            'call_id': 72,
            'source': '99988526423',
            'destination': '9993468278',
        },
        {
            'type': 'end',
            'timestamp': '2017-12-12T22:50:56Z',
            'call_id': 72,
        }
    ),
    (
        {
            'type': 'start',
            'timestamp': '2017-12-12T21:57:13Z',
            'call_id': 73,
            'source': '99988526423',
            'destination': '9993468278',
        },
        {
            'type': 'end',
            'timestamp': '2017-12-12T22:10:56Z',
            'call_id': 73,
        }
    ),
    (
        {
            'type': 'start',
            'timestamp': '2017-12-12T04:57:13Z',
            'call_id': 74,
            'source': '99988526423',
            'destination': '9993468278',
        },
        {
            'type': 'end',
            'timestamp': '2017-12-12T06:10:56Z',
            'call_id': 74,
        }
    ),
    (
        {
            'type': 'start',
            'timestamp': '2017-12-13T21:57:13Z',
            'call_id': 75,
            'source': '99988526423',
            'destination': '9993468278',
        },
        {
            'type': 'end',
            'timestamp': '2017-12-14T22:10:56Z',
            'call_id': 75,
        }
    ),
    (
        {
            'type': 'start',
            'timestamp': '2017-12-12T15:07:58Z',
            'call_id': 76,
            'source': '99988526423',
            'destination': '9993468278',
        },
        {
            'type': 'end',
            'timestamp': '2017-12-12T15:12:56Z',
            'call_id': 76,
        }
    ),
    (
        {
            'type': 'start',
            'timestamp': '2018-02-28T21:57:13Z',
            'call_id': 77,
            'source': '99988526423',
            'destination': '9993468278',
        },
        {
            'type': 'end',
            'timestamp': '2018-03-01T22:10:56Z',
            'call_id': 77,
        }
    ),
)

prices = (
    {
        "tariff_type": "standard",
        "start_time": "06:00",
        "end_time": "22:00",
        "standing_charge": "0.36",
        "call_charge": "0.09"
    },
    {
        "tariff_type": "reduced",
        "start_time": "22:00",
        "end_time": "06:00",
        "standing_charge": "0.36",
        "call_charge": "0.00"
    },
)


def send_post(payload, url):
    response = requests.post(url, json=payload, headers=HEADERS)
    if response.status_code != 201:
        pdb.set_trace()

    return response.json()


def remove_fields(payload, fields):
    for field in fields:
        payload.pop(field)


def iso8601_to_epoch(datestring):
    """
    iso8601_to_epoch - convert the iso8601 date into the unix epoch time

    >>> iso8601_to_epoch("2012-07-09T22:27:50.272517")
    1341872870
    """
    epoch = calendar.timegm(datetime.strptime(datestring, "%Y-%m-%dT%H:%M:%SZ").utctimetuple())
    return epoch


if __name__ == '__main__':
    for start, end in payloads:
        send_post(start, URL_START)
        send_post(end, URL_END)
