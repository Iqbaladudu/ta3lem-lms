# Generated migration for dual pricing system

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('courses', '0013_course_pricing_type'),  # Fixed: correct dependency
        ('subscriptions', '0001_initial'),
        ('payments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='courseenrollment',
            name='access_type',
            field=models.CharField(
                choices=[
                    ('free', 'Free Access'),
                    ('purchased', 'One-Time Purchase'),
                    ('subscription', 'Subscription Access')
                ],
                default='free',
                max_length=20,
                help_text='How this enrollment was granted'
            ),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='subscription',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='course_enrollments',
                to='subscriptions.usersubscription',
                help_text='Subscription that grants access (if applicable)'
            ),
        ),
        migrations.AddField(
            model_name='courseenrollment',
            name='order',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='course_enrollments',
                to='payments.order',
                help_text='Order for one-time purchase (if applicable)'
            ),
        ),
    ]
