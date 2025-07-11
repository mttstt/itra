# Generated by Django 5.2.3 on 2025-07-04 20:36

import django.db.models.deletion
import mptt.fields
import simple_history.models
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('campagne', '0001_initial'),
        ('elementtypes', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Asset',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome Asset')),
                ('descrizione', models.TextField(blank=True, verbose_name='Descrizione')),
                ('cmdb', models.CharField(blank=True, max_length=100, verbose_name='ID CMDB')),
                ('legal_entity', models.CharField(blank=True, max_length=100, verbose_name='Legal Entity')),
                ('status', models.CharField(choices=[('in_produzione', 'In Produzione'), ('in_sviluppo', 'In Sviluppo'), ('dismesso', 'Dismesso')], default='in_sviluppo', max_length=20, verbose_name='Stato')),
                ('campagna', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='assets', to='campagne.campagna')),
                ('cloned_from', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clones', to='assets.asset')),
                ('responsabile_applicativo', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asset_applicativo', to=settings.AUTH_USER_MODEL)),
                ('utente_responsabile', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='asset_responsabile', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'Asset',
                'verbose_name_plural': 'Assets',
            },
        ),
        migrations.CreateModel(
            name='NodoStruttura',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome_specifico', models.CharField(blank=True, max_length=255, verbose_name='Nome Specifico')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('asset', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nodi_struttura', to='assets.asset')),
                ('campagna', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='campagne.campagna')),
                ('element_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nodi_istanziati', to='elementtypes.elementtype')),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='assets.nodostruttura')),
            ],
            options={
                'verbose_name': 'Nodo di Struttura',
                'verbose_name_plural': 'Nodi di Struttura',
                'unique_together': {('asset', 'element_type', 'parent')},
            },
        ),
        migrations.CreateModel(
            name='HistoricalNodoStruttura',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('nome_specifico', models.CharField(blank=True, max_length=255, verbose_name='Nome Specifico')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('asset', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='assets.asset')),
                ('campagna', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='campagne.campagna')),
                ('element_type', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='elementtypes.elementtype')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='assets.nodostruttura')),
            ],
            options={
                'verbose_name': 'historical Nodo di Struttura',
                'verbose_name_plural': 'historical Nodi di Struttura',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='StrutturaTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome Template')),
                ('descrizione', models.TextField(blank=True, verbose_name='Descrizione')),
                ('campagna', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='templates_struttura', to='campagne.campagna')),
                ('cloned_from', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='clones', to='assets.strutturatemplate')),
            ],
            options={
                'verbose_name': 'Template di Struttura',
                'verbose_name_plural': 'Template di Struttura',
                'unique_together': {('nome', 'campagna')},
            },
        ),
        migrations.CreateModel(
            name='NodoTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('lft', models.PositiveIntegerField(editable=False)),
                ('rght', models.PositiveIntegerField(editable=False)),
                ('tree_id', models.PositiveIntegerField(db_index=True, editable=False)),
                ('level', models.PositiveIntegerField(editable=False)),
                ('campagna', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='+', to='campagne.campagna')),
                ('element_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='elementtypes.elementtype')),
                ('parent', mptt.fields.TreeForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='children', to='assets.nodotemplate')),
                ('template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='nodi_template', to='assets.strutturatemplate')),
            ],
            options={
                'verbose_name': 'Nodo di Template',
                'verbose_name_plural': 'Nodi di Template',
                'unique_together': {('template', 'element_type', 'parent')},
            },
        ),
        migrations.CreateModel(
            name='HistoricalStrutturaTemplate',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome Template')),
                ('descrizione', models.TextField(blank=True, verbose_name='Descrizione')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('campagna', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='campagne.campagna')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('cloned_from', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='assets.strutturatemplate')),
            ],
            options={
                'verbose_name': 'historical Template di Struttura',
                'verbose_name_plural': 'historical Template di Struttura',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalNodoTemplate',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('campagna', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='campagne.campagna')),
                ('element_type', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='elementtypes.elementtype')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('parent', mptt.fields.TreeForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='assets.nodotemplate')),
                ('template', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='assets.strutturatemplate')),
            ],
            options={
                'verbose_name': 'historical Nodo di Template',
                'verbose_name_plural': 'historical Nodi di Template',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.CreateModel(
            name='HistoricalAsset',
            fields=[
                ('id', models.BigIntegerField(auto_created=True, blank=True, db_index=True, verbose_name='ID')),
                ('nome', models.CharField(max_length=255, verbose_name='Nome Asset')),
                ('descrizione', models.TextField(blank=True, verbose_name='Descrizione')),
                ('cmdb', models.CharField(blank=True, max_length=100, verbose_name='ID CMDB')),
                ('legal_entity', models.CharField(blank=True, max_length=100, verbose_name='Legal Entity')),
                ('status', models.CharField(choices=[('in_produzione', 'In Produzione'), ('in_sviluppo', 'In Sviluppo'), ('dismesso', 'Dismesso')], default='in_sviluppo', max_length=20, verbose_name='Stato')),
                ('history_id', models.AutoField(primary_key=True, serialize=False)),
                ('history_date', models.DateTimeField(db_index=True)),
                ('history_change_reason', models.CharField(max_length=100, null=True)),
                ('history_type', models.CharField(choices=[('+', 'Created'), ('~', 'Changed'), ('-', 'Deleted')], max_length=1)),
                ('campagna', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='campagne.campagna')),
                ('cloned_from', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='assets.asset')),
                ('history_user', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('responsabile_applicativo', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('utente_responsabile', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to=settings.AUTH_USER_MODEL)),
                ('template_da_applicare', models.ForeignKey(blank=True, db_constraint=False, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='+', to='assets.strutturatemplate', verbose_name='Template di Struttura')),
            ],
            options={
                'verbose_name': 'historical Asset',
                'verbose_name_plural': 'historical Assets',
                'ordering': ('-history_date', '-history_id'),
                'get_latest_by': ('history_date', 'history_id'),
            },
            bases=(simple_history.models.HistoricalChanges, models.Model),
        ),
        migrations.AddField(
            model_name='asset',
            name='template_da_applicare',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='assets.strutturatemplate', verbose_name='Template di Struttura'),
        ),
        migrations.AlterUniqueTogether(
            name='asset',
            unique_together={('nome', 'campagna')},
        ),
    ]
