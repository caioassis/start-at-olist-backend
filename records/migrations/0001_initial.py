# Generated by Django 2.2.11 on 2020-03-10 19:14

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='CallEndRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('call_id', models.CharField(max_length=50, unique=True, verbose_name='Call Unique ID')),
                ('timestamp', models.DateTimeField(blank=True, verbose_name='Timestamp')),
                ('price', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True, verbose_name='Price')),
            ],
        ),
        migrations.CreateModel(
            name='CallStartRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('call_id', models.CharField(max_length=50, unique=True, verbose_name='Call Unique ID')),
                ('timestamp', models.DateTimeField(blank=True, verbose_name='Timestamp')),
                ('source', models.CharField(max_length=30, verbose_name='Source')),
                ('destination', models.CharField(max_length=11, validators=[django.core.validators.MinLengthValidator(10), django.core.validators.MaxLengthValidator(11), django.core.validators.RegexValidator(message='Destination must contain only numbers.', regex='^\\d+$')], verbose_name='Destination')),
            ],
        ),
        migrations.AddConstraint(
            model_name='callstartrecord',
            constraint=models.UniqueConstraint(fields=('call_id',), name='callstartrecord_unique_callid'),
        ),
        migrations.AddConstraint(
            model_name='callendrecord',
            constraint=models.UniqueConstraint(fields=('call_id',), name='callendrecord_unique_callid'),
        ),
    ]
