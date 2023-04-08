# Generated by Django 4.1.7 on 2023-03-18 23:15

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api', '0007_remove_shop_user_remove_category_shops_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='product',
            name='price_rrc',
        ),
        migrations.RemoveField(
            model_name='userprofile',
            name='state',
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='user',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='user_profile', to=settings.AUTH_USER_MODEL),
        ),
    ]
