from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import re

User = get_user_model()


class Command(BaseCommand):
    help = 'Normalize all existing user phone numbers to international +254 format'

    def add_arguments(self, parser):
        parser.add_argument('--dry-run', action='store_true', help='Show what changes would be made without saving to DB')

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        updated_count = 0

        for user in User.objects.all():
            if not user.phone_number:
                continue

            raw = user.phone_number.strip()
            cleaned = re.sub(r'[\s\-\(\)]', '', raw)
            normalized = None

            if re.match(r'^(07|01)\d{8}$', cleaned):
                normalized = '+254' + cleaned[1:]
            elif re.match(r'^254(7|1)\d{8}$', cleaned):
                normalized = '+' + cleaned
            
            if normalized and normalized != user.phone_number:
                self.stdout.write(f"User ID {user.id} ({user.username}): '{user.phone_number}' -> '{normalized}'")
                if not dry_run:
                    # Ensure no uniqueness collision before updating
                    if not User.objects.filter(phone_number=normalized).exclude(pk=user.pk).exists():
                        user.phone_number = normalized
                        user.save()
                        updated_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(f"Collision error for User ID {user.id}: {normalized} already exists for another user."))
                else:
                    updated_count += 1

        if dry_run:
            self.stdout.write(self.style.SUCCESS(f"Dry run complete. {updated_count} user phone numbers would be normalized."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Successfully normalized {updated_count} user phone numbers."))
