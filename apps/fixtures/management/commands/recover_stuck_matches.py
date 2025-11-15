"""
Management command to detect and recover stuck matches
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.fixtures.services import APIFootballService


class Command(BaseCommand):
    help = 'Detect and recover matches that are stuck in live status'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-recoveries',
            type=int,
            default=20,
            help='Maximum number of matches to attempt recovery for (default: 20)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show stuck matches without attempting recovery'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force recovery even with low API quota (use with caution)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('=' * 60)
        )
        self.stdout.write(
            self.style.SUCCESS('STUCK MATCH RECOVERY STARTED')
        )
        self.stdout.write(
            self.style.SUCCESS(f'Time: {timezone.now()}')
        )
        self.stdout.write(
            self.style.SUCCESS('=' * 60)
        )

        api_service = APIFootballService()
        
        # Check API usage
        stats = api_service.get_api_usage_stats()
        self.stdout.write(f"API Usage: {stats['api_requests']}/{stats['limit']} requests today")
        self.stdout.write(f"Remaining: {stats['remaining']} requests")
        
        # Check if we can proceed
        min_quota = 10 if not options['force'] else 1
        if stats['remaining'] < min_quota and not options['dry_run']:
            self.stdout.write(
                self.style.ERROR(f'Insufficient API quota (need at least {min_quota})')
            )
            self.stdout.write(
                self.style.WARNING('Use --force to override or --dry-run to see stuck matches without API calls')
            )
            return

        # Detect stuck matches
        stuck_matches = api_service.detect_stuck_matches()
        
        if stuck_matches.count() == 0:
            self.stdout.write(self.style.SUCCESS('✓ No stuck matches found - all good!'))
            return
            
        self.stdout.write(
            self.style.WARNING(f'Found {stuck_matches.count()} potentially stuck matches:')
        )
        
        for i, match in enumerate(stuck_matches[:options['max_recoveries']], 1):
            match_duration = (timezone.now() - match.date).total_seconds() / 60
            self.stdout.write(
                f"  {i}. {match.home_team.name} vs {match.away_team.name} "
                f"({match.status_short}, {match.elapsed}min) - "
                f"Started {match_duration:.0f}min ago - API ID: {match.api_id}"
            )
        
        if stuck_matches.count() > options['max_recoveries']:
            remaining = stuck_matches.count() - options['max_recoveries']
            self.stdout.write(f"     ...and {remaining} more")
            
        if options['dry_run']:
            self.stdout.write(self.style.SUCCESS('\n--dry-run enabled, no recovery attempted'))
            return
            
        # Attempt recovery
        self.stdout.write('\nAttempting recovery...\n')
        
        recovery_stats = {
            'attempted': 0,
            'recovered_successfully': 0,
            'recovery_failed': 0,
            'api_requests_used': 0
        }
        
        for match in stuck_matches[:options['max_recoveries']]:
            recovery_stats['attempted'] += 1
            
            if api_service.recover_stuck_match(match):
                recovery_stats['recovered_successfully'] += 1
            else:
                recovery_stats['recovery_failed'] += 1
            recovery_stats['api_requests_used'] += 1
            
            # Check if we're running low on API quota
            if not options['force'] and APIFootballService().get_api_usage_stats()['remaining'] < 5:
                self.stdout.write(self.style.WARNING('Stopping recovery - API quota running low'))
                break
        
        # Summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('RECOVERY SUMMARY:')
        self.stdout.write(f"  Stuck matches found: {stuck_matches.count()}")
        self.stdout.write(f"  Recovery attempted: {recovery_stats['attempted']}")
        self.stdout.write(f"  Successfully recovered: {recovery_stats['recovered_successfully']}")
        self.stdout.write(f"  Recovery failed: {recovery_stats['recovery_failed']}")
        self.stdout.write(f"  API requests used: {recovery_stats['api_requests_used']}")
        
        if recovery_stats['recovered_successfully'] > 0:
            self.stdout.write(
                self.style.SUCCESS(f"\n✓ Successfully recovered {recovery_stats['recovered_successfully']} stuck matches!")
            )
        elif recovery_stats['attempted'] == 0:
            self.stdout.write(self.style.SUCCESS('\n✓ No recovery needed'))
        else:
            self.stdout.write(
                self.style.ERROR(f"\n❌ All {recovery_stats['attempted']} recovery attempts failed")
            )
            
        self.stdout.write('=' * 60)