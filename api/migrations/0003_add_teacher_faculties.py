from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api', '0002_create_initial_groups'),
    ]

    operations = [
        migrations.AddField(
            model_name='teacher',
            name='faculties',
            field=models.ManyToManyField(blank=True, related_name='teachers', to='api.Faculty'),
        ),
    ]
