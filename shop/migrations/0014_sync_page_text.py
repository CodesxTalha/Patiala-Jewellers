from django.db import migrations


def sync(apps, schema_editor):
    from shop.content import DEFAULTS
    ContentBlock = apps.get_model("shop", "ContentBlock")
    for key, (group, label, text) in DEFAULTS.items():
        ContentBlock.objects.get_or_create(key=key, defaults={"group": group, "label": label, "text": text})


class Migration(migrations.Migration):

    dependencies = [("shop", "0013_page_text_and_hero")]
    operations = [migrations.RunPython(sync, migrations.RunPython.noop)]
