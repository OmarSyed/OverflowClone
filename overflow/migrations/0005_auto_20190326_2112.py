# Generated by Django 2.1.7 on 2019-03-27 01:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('overflow', '0004_auto_20190326_1756'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='comment_url',
            field=models.CharField(default='DNmFhmhqd9JE88T', max_length=15),
        ),
    ]
