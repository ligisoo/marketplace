import os
import tempfile
from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.db import connection
from django.conf import settings
from apps.users.models import User, UserProfile


class Command(BaseCommand):
    help = 'Refreshes the database while preserving user information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to refresh the database (required for safety)',
        )
        parser.add_argument(
            '--backup-users',
            action='store_true',
            help='Create a backup of user data before refresh (recommended)',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            raise CommandError(
                'This command will delete all data except users. '
                'Use --confirm to proceed.'
            )

        self.stdout.write('Starting database refresh...')
        
        # Step 1: Backup user data if requested
        user_backup = None
        if options['backup_users']:
            self.stdout.write('Creating backup of user data...')
            user_backup = self._backup_users()
            self.stdout.write(self.style.SUCCESS(f'Backed up {len(user_backup)} users'))

        try:
            # Step 2: Export user data
            self.stdout.write('Exporting current user data...')
            users_data = self._export_users()
            self.stdout.write(self.style.SUCCESS(f'Exported {len(users_data)} users'))

            # Step 3: Flush the database (removes all data)
            self.stdout.write('Flushing database...')
            call_command('flush', '--noinput')
            self.stdout.write(self.style.SUCCESS('Database flushed'))

            # Step 4: Run migrations to recreate tables
            self.stdout.write('Running migrations...')
            call_command('migrate', '--noinput')
            self.stdout.write(self.style.SUCCESS('Migrations completed'))

            # Step 5: Restore user data
            self.stdout.write('Restoring user data...')
            restored_count = self._restore_users(users_data)
            self.stdout.write(self.style.SUCCESS(f'Restored {restored_count} users'))

            self.stdout.write(self.style.SUCCESS('Database refresh completed successfully!'))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during database refresh: {str(e)}')
            )
            if user_backup:
                self.stdout.write('User backup is available for manual recovery.')
            raise

    def _export_users(self):
        """Export all user and user profile data"""
        users_data = []
        
        for user in User.objects.all():
            user_data = {
                'id': user.id,
                'phone_number': user.phone_number,
                'email': user.email,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'is_active': user.is_active,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'date_joined': user.date_joined.isoformat(),
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'password': user.password,  # Keep hashed password
            }
            
            # Add profile data if it exists
            if hasattr(user, 'userprofile'):
                profile = user.userprofile
                user_data['profile'] = {
                    'is_buyer': profile.is_buyer,
                    'is_tipster': profile.is_tipster,
                    'bio': profile.bio,
                    'profile_picture': profile.profile_picture.name if profile.profile_picture else None,
                    'wallet_balance': str(profile.wallet_balance),
                    'is_verified': profile.is_verified,
                    'verification_date': profile.verification_date.isoformat() if profile.verification_date else None,
                    'created_at': profile.created_at.isoformat(),
                    'updated_at': profile.updated_at.isoformat(),
                }
            
            users_data.append(user_data)
        
        return users_data

    def _restore_users(self, users_data):
        """Restore user and user profile data"""
        from django.utils.dateparse import parse_datetime
        from decimal import Decimal
        
        restored_count = 0
        
        for user_data in users_data:
            # Create user
            user = User(
                id=user_data['id'],
                phone_number=user_data['phone_number'],
                email=user_data['email'],
                username=user_data['username'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                is_active=user_data['is_active'],
                is_staff=user_data['is_staff'],
                is_superuser=user_data['is_superuser'],
                date_joined=parse_datetime(user_data['date_joined']),
                last_login=parse_datetime(user_data['last_login']) if user_data['last_login'] else None,
                password=user_data['password'],
            )
            user.save()
            
            # Create/update profile if data exists
            if 'profile' in user_data:
                profile_data = user_data['profile']
                
                # Get or create profile (should be created by signal, but ensure it exists)
                profile, created = UserProfile.objects.get_or_create(
                    user=user,
                    defaults={
                        'is_buyer': profile_data['is_buyer'],
                        'is_tipster': profile_data['is_tipster'],
                        'bio': profile_data['bio'],
                        'wallet_balance': Decimal(profile_data['wallet_balance']),
                        'is_verified': profile_data['is_verified'],
                        'verification_date': parse_datetime(profile_data['verification_date']) if profile_data['verification_date'] else None,
                        'created_at': parse_datetime(profile_data['created_at']),
                        'updated_at': parse_datetime(profile_data['updated_at']),
                    }
                )
                
                if not created:
                    # Update existing profile
                    profile.is_buyer = profile_data['is_buyer']
                    profile.is_tipster = profile_data['is_tipster']
                    profile.bio = profile_data['bio']
                    profile.wallet_balance = Decimal(profile_data['wallet_balance'])
                    profile.is_verified = profile_data['is_verified']
                    profile.verification_date = parse_datetime(profile_data['verification_date']) if profile_data['verification_date'] else None
                    profile.created_at = parse_datetime(profile_data['created_at'])
                    profile.updated_at = parse_datetime(profile_data['updated_at'])
                    profile.save()
            
            restored_count += 1
        
        return restored_count

    def _backup_users(self):
        """Create a backup file of user data"""
        import json
        from datetime import datetime
        
        users_data = self._export_users()
        
        # Create backup file
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = os.path.join(backup_dir, f'users_backup_{timestamp}.json')
        
        with open(backup_file, 'w') as f:
            json.dump(users_data, f, indent=2, default=str)
        
        self.stdout.write(f'User backup saved to: {backup_file}')
        return users_data