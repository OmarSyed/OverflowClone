# Generated by Django 2.1.7 on 2019-04-09 23:05

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('overflow', '0013_auto_20190409_1407'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='comment_url',
            field=models.CharField(default='YMOVAwOVzbeqcmD', max_length=15),
        ),
        migrations.AlterField(
            model_name='post',
            name='body',
            field=models.TextField(),
        ),
    ]