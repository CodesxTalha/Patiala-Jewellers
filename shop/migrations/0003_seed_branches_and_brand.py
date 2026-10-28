from django.db import migrations

BRANCHES = ["PWD", "DHA II", "Ghauri Town", "F-7"]


def seed(apps, schema_editor):
    Branch = apps.get_model("shop", "Branch")
    StoreInfo = apps.get_model("shop", "StoreInfo")

    if not Branch.objects.exists():
        for i, name in enumerate(BRANCHES):
            Branch.objects.create(name=name, city="Islamabad", display_order=i)

    # Fix the old spelling on an existing store record, if there is one.
    StoreInfo.objects.filter(name="Patiala Jewellers").update(
        name="Patiala Jewelers", tagline="Made to be passed down."
    )


class Migration(migrations.Migration):

    dependencies = [
        ("shop", "0002_brand_guide"),
    ]

    operations = [
        migrations.RunPython(seed, migrations.RunPython.noop),
    ]
