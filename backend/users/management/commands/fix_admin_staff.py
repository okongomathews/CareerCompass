"""
Management command: fix_admin_staff
Usage: python manage.py fix_admin_staff

Grants is_staff=True to all users whose user_type='admin' so they can
access the Django admin panel at /admin/.
Run this once after upgrading to the version that adds the pre_save signal.
"""
from django.core.management.base import BaseCommand
from users.models import CustomUser


class Command(BaseCommand):
    help = "Set is_staff=True on all admin-type users so they can access /admin/"

    def handle(self, *args, **options):
        updated = CustomUser.objects.filter(
            user_type='admin', is_staff=False
        ).update(is_staff=True)
        self.stdout.write(
            self.style.SUCCESS(
                f"Done. Updated {updated} admin user(s) → is_staff=True.\n"
                "They can now log in to /admin/ using their existing credentials."
            )
        )
