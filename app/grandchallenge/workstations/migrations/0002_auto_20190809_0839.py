# Generated by Django 2.2.4 on 2019-08-09 08:39

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("auth", "0011_update_proxy_permissions"),
        ("workstations", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="workstation",
            name="editors_group",
            field=models.OneToOneField(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="editors_of_workstation",
                to="auth.Group",
            ),
        ),
        migrations.AddField(
            model_name="workstation",
            name="users_group",
            field=models.OneToOneField(
                editable=False,
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                related_name="users_of_workstation",
                to="auth.Group",
            ),
        ),
    ]