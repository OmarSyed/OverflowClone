# Generated by Django 2.1.7 on 2019-03-27 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('overflow', '0008_auto_20190327_1537'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='comment_url',
            field=models.CharField(default='DeTLPrK7IQgwhRo', max_length=15),
        ),
        migrations.AlterField(
            model_name='comment',
            name='time_posted',
            field=models.IntegerField(default=0),
        ),
        migrations.AlterField(
            model_name='post',
            name='time_added',
            field=models.IntegerField(default=0),
        ),
    ]
