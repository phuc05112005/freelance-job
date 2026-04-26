from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("jobs", "0011_employmenttype_experiencelevel_workmode_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="job",
            name="brand_image",
            field=models.ImageField(
                blank=True,
                help_text="Anh thuong hieu/cong ty (khong bat buoc)",
                null=True,
                upload_to="jobs/brands/",
            ),
        ),
    ]
