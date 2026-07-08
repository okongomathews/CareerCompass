"""
Migrate legacy user_type values (school, teacher, parent) to the current
three-role system (user, student, admin).

Run once after upgrading:
    python manage.py migrate_user_types
"""
from django.core.management.base import BaseCommand
from users.models import CustomUser


MAPPING = {
    'school':  'user',    # school admins → general user
    'teacher': 'user',    # teachers → general user
    'parent':  'user',    # parents → general user
}


class Command(BaseCommand):
    help = 'Migrate legacy user_type values to the current user/student/admin system'

    def handle(self, *args, **options):
        total = 0
        for old_type, new_type in MAPPING.items():
            qs = CustomUser.objects.filter(user_type=old_type)
            count = qs.count()
            if count:
                qs.update(user_type=new_type)
                self.stdout.write(
                    self.style.SUCCESS(f"  {count} '{old_type}' users → '{new_type}'")
                )
                total += count
        if total:
            self.stdout.write(self.style.SUCCESS(f'Done. {total} user(s) migrated.'))
        else:
            self.stdout.write('No legacy user types found — nothing to migrate.')
