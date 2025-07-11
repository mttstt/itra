# Generated by Django 5.2.3 on 2025-07-01 13:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('campagne', '0001_initial'),
        ('controlli', '0001_initial'),
        ('elementtypes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='controllo',
            name='elementtype',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='controls_assigned_to_elementtype', to='elementtypes.elementtype', verbose_name='Element Type'),
        ),
        migrations.AddField(
            model_name='controllo',
            name='owner',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL, verbose_name='Owner del controllo'),
        ),
        migrations.AddField(
            model_name='historicalcontrollo',
            name='campagna',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='campagne.campagna'),
        ),
        migrations.AddField(
            model_name='historicalcontrollo',
            name='elementtype',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='elementtypes.elementtype', verbose_name='Element Type'),
        ),
        migrations.AddField(
            model_name='historicalcontrollo',
            name='history_user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='historicalcontrollo',
            name='owner',
            field=models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL, verbose_name='Owner del controllo'),
        ),
        migrations.AlterUniqueTogether(
            name='controllo',
            unique_together={('nome', 'campagna')},
        ),
    ]
