# Generated by Django 2.2 on 2019-04-28 22:04

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('overflow', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Media',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('file_id', models.CharField(max_length=100)),
                ('file_name', models.TextField()),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='has_media',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='post',
            name='solved',
            field=models.BooleanField(default=False),
        ),
        migrations.AlterField(
            model_name='comment',
            name='comment_url',
            field=models.CharField(default='Xuj08zasg1cDLjU', max_length=15),
        ),
        migrations.CreateModel(
            name='QuestionMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='overflow.Media')),
                ('question', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='overflow.Post')),
            ],
        ),
        migrations.CreateModel(
            name='CommentMedia',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('comment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='overflow.Comment')),
                ('media', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='overflow.Media')),
            ],
        ),
    ]
