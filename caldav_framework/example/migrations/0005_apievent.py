# Generated by Django 3.2 on 2022-12-11 08:28

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('example', '0004_alter_calendar_color'),
    ]

    operations = [
        migrations.CreateModel(
            name='APIEvent',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('example.event',),
        ),
    ]
