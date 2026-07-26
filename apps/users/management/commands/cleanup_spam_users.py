from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.users.forms import DISPOSABLE_EMAIL_DOMAINS

User = get_user_model()


class Command(BaseCommand):
    help = 'Deactivate or delete suspicious/spam user accounts'

    def add_arguments(self, parser):
        parser.add_argument('--phone', type=str, help='Specific phone number to purge/deactivate')
        parser.add_argument('--email', type=str, help='Specific email address to purge/deactivate')
        parser.add_argument('--username', type=str, help='Specific username to purge/deactivate')
        parser.add_argument('--delete', action='store_true', help='Permanently delete matching users instead of deactivating')
        parser.add_argument('--scan', action='store_true', help='Scan for users with disposable emails or invalid NANP area codes')

    def handle(self, *args, **options):
        users_to_process = User.objects.none()

        if options['phone']:
            users_to_process |= User.objects.filter(phone_number__icontains=options['phone'])
        
        if options['email']:
            users_to_process |= User.objects.filter(email__iexact=options['email'])

        if options['username']:
            users_to_process |= User.objects.filter(username__iexact=options['username'])

        if options['scan']:
            # Scan for disposable email domains
            for domain in DISPOSABLE_EMAIL_DOMAINS:
                users_to_process |= User.objects.filter(email__icontains=f"@{domain}")

            # Scan for invalid area codes (e.g., +1483...)
            users_to_process |= User.objects.filter(phone_number__icontains="+1-483")
            users_to_process |= User.objects.filter(phone_number__icontains="+1483")

        users = users_to_process.distinct()

        if not users.exists():
            self.stdout.write(self.style.WARNING("No matching spam users found."))
            return

        for user in users:
            details = f"ID={user.id} | Phone={user.phone_number} | Username={user.username} | Email={user.email}"
            if options['delete']:
                user.delete()
                self.stdout.write(self.style.SUCCESS(f"Deleted spam user: {details}"))
            else:
                user.is_active = False
                user.save()
                self.stdout.write(self.style.SUCCESS(f"Deactivated spam user: {details}"))
