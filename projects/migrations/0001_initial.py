# Generated by Django 2.2.3 on 2019-08-08 21:32

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=29)),
                ('description', models.CharField(default='', max_length=1000000000)),
                ('public', models.BooleanField(default=False)),
            ],
        ),
        migrations.CreateModel(
            name='ProjectUser',
            fields=[
                ('id', models.BigIntegerField(primary_key=True, serialize=False)),
                ('role', models.CharField(default='', max_length=100)),
                ('project', models.CharField(max_length=29)),
                ('owner', models.BooleanField(default=False)),
                ('public', models.BooleanField(default=True)),
                ('permissions', models.SmallIntegerField(default=0)),
            ],
        ),
    ]
