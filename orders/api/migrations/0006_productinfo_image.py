# Generated by Django 4.1.7 on 2023-03-18 21:53

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0005_alter_confirmedbasket_options_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productinfo',
            name='image',
            field=models.ImageField(default=2, upload_to=''),
            preserve_default=False,
        ),
    ]
