"""
Migration 0003 – Fix AssessmentResult schema drift.

The initial migrations were generated before the model was finalised.
Three differences exist between 0001_initial and models.py:

  1. ei_score / sn_score / tf_score / jp_score:
       migration → max_digits=5  (sufficient for [-100, 100] but out of sync)
       model     → max_digits=6
  2. confidence:
       migration → max_digits=3  (sufficient for [0.0, 1.0])
       model     → max_digits=4
  3. updated_at:
       migration → missing entirely  ← causes OperationalError on every save()
       model     → DateTimeField(auto_now=True)

Bug impact: any call to AssessmentResult.save() (including update_or_create in
MBTICalculator.generate_result) raises:
    OperationalError: table assessments_assessmentresult has no column named updated_at
making it impossible to complete an assessment.
"""

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("assessments", "0002_initial"),
    ]

    operations = [
        # 1. Add the missing updated_at column.
        #    Use auto_now=False here and handle auto_now via the model; for the
        #    migration we just need the column to exist with a sensible default.
        migrations.AddField(
            model_name="assessmentresult",
            name="updated_at",
            field=models.DateTimeField(auto_now=True),
        ),
        # 2. Widen score columns from max_digits=5 to max_digits=6 to match model.
        migrations.AlterField(
            model_name="assessmentresult",
            name="ei_score",
            field=models.DecimalField(max_digits=6, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="assessmentresult",
            name="sn_score",
            field=models.DecimalField(max_digits=6, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="assessmentresult",
            name="tf_score",
            field=models.DecimalField(max_digits=6, decimal_places=2),
        ),
        migrations.AlterField(
            model_name="assessmentresult",
            name="jp_score",
            field=models.DecimalField(max_digits=6, decimal_places=2),
        ),
        # 3. Widen confidence from max_digits=3 to max_digits=4 to match model.
        migrations.AlterField(
            model_name="assessmentresult",
            name="confidence",
            field=models.DecimalField(max_digits=4, decimal_places=2),
        ),
    ]
