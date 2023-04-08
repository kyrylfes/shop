# Generated by Django 4.1.7 on 2023-03-18 21:17

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0004_alter_basket_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='confirmedbasket',
            options={'verbose_name': 'Confirmed order', 'verbose_name_plural': 'Confirmed orders'},
        ),
        migrations.AlterField(
            model_name='confirmedbasket',
            name='mail',
            field=models.CharField(choices=[('нова почта', 'Нова почта'), ('укр почта', 'Укр почта')], default='нова почта', max_length=30),
        ),
        migrations.AlterField(
            model_name='productinfo',
            name='product',
            field=models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='product_info', to='api.product'),
        ),
    ]
