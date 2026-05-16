from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0013_alter_job_brand_image_favoritejob'),
        ('users', '0017_alter_cv_email'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='related_category',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='students',
                to='jobs.jobcategory',
            ),
        ),
    ]
