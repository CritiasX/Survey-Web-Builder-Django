# Generated migration to rename app from landingPage to WebSurvey

from django.db import migrations


def update_contenttypes(apps, schema_editor):
    """Update the content types table to reflect the new app name."""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    db_alias = schema_editor.connection.alias
    ContentType.objects.using(db_alias).filter(app_label='landingPage').update(app_label='WebSurvey')


def update_contenttypes_reverse(apps, schema_editor):
    """Reverse the content type update."""
    ContentType = apps.get_model('contenttypes', 'ContentType')
    db_alias = schema_editor.connection.alias
    ContentType.objects.using(db_alias).filter(app_label='WebSurvey').update(app_label='landingPage')


class Migration(migrations.Migration):

    dependencies = [
        ('WebSurvey', '0001_initial'),
        ('contenttypes', '__latest__'),
    ]

    operations = [
        migrations.RunPython(update_contenttypes, update_contenttypes_reverse),
    ]

