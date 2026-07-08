"""
Change AssessmentResult.personality_type from CASCADE to PROTECT.

Previously, running `python manage.py load_mbti_data` would call
PersonalityType.objects.all().delete() which cascaded and silently
wiped every AssessmentResult in the database.

PROTECT prevents that deletion from ever succeeding — Django will raise
a ProtectedError instead, making the problem visible rather than silent.
"""
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('assessments', '0004_alter_question_dimension_a_weight'),
    ]

    operations = [
        migrations.AlterField(
            model_name='assessmentresult',
            name='personality_type',
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                to='assessments.personalitytype',
            ),
        ),
    ]
