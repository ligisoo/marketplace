import os
import sys
import django

# Setup Django environment
sys.path.insert(0, os.path.abspath(os.path.dirname(os.path.dirname(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
django.setup()

from apps.tips.models import Tip, TipMatch
from apps.tips.services import ResultVerifier
from apps.fixtures.models import Fixture

def main():
    verifier = ResultVerifier()
    # Check all matches of active or previously resulted tips
    matches_to_reverify = TipMatch.objects.filter(tip__status__in=['active', 'archived'])
    
    print(f"Scanning {matches_to_reverify.count()} matches for corrections & grading...")
    reverified_count = 0
    tips_updated = set()

    for match in matches_to_reverify:
        fixture = None
        
        # 1. Try to find the fixture
        if match.api_match_id:
            try:
                fixture = Fixture.objects.filter(api_id=int(match.api_match_id)).first()
            except ValueError:
                pass
        
        # 2. If not linked, try fuzzy matching to find the fixture in the database
        if not fixture:
            fixture = verifier._find_matching_fixture(match)
            if fixture:
                match.api_match_id = str(fixture.api_id)
                match.save(update_fields=['api_match_id'])
                print(f"🔗 Linked Match {match.id} ({match.home_team} vs {match.away_team}) to Fixture ID {fixture.api_id}")
        
        # 3. If we have a finished fixture, check/update results
        if fixture and fixture.is_finished:
            new_won = verifier._check_market_result(
                match.market,
                match.selection,
                fixture.home_goals,
                fixture.away_goals,
                home_team=match.home_team,
                away_team=match.away_team
            )
            
            # Update if result changed or if it wasn't resulted yet
            if not match.is_resulted or new_won != match.is_won:
                action_word = "corrected" if match.is_resulted else "resolved"
                print(f"✓ Match {match.id} ({match.home_team} vs {match.away_team}): is_won {action_word} from {match.is_won} to {new_won} (Result: {fixture.get_result_string()})")
                match.is_won = new_won
                match.is_resulted = True
                match.actual_result = fixture.get_result_string()
                match.save(update_fields=['is_won', 'is_resulted', 'actual_result'])
                reverified_count += 1
                tips_updated.add(match.tip)

    # Re-evaluate parent tips
    for tip in tips_updated:
        all_matches = tip.matches.all()
        # A tip is fully resulted only if all of its matches are resulted
        all_resulted = all(m.is_resulted for m in all_matches)
        
        if all_resulted:
            tip_won = all(m.is_won for m in all_matches)
            
            if not tip.is_resulted or tip.is_won != tip_won:
                print(f"✓ Parent Tip {tip.id} ({tip.bet_code}): marked as fully resulted. won={tip_won}")
                tip.is_resulted = True
                tip.is_won = tip_won
                tip.status = 'archived'
                from django.utils import timezone
                tip.result_verified_at = timezone.now()
                tip.save(update_fields=['is_resulted', 'is_won', 'status', 'result_verified_at'])

    print(f"Done! Updated/corrected {reverified_count} matches across {len(tips_updated)} tips.")

if __name__ == '__main__':
    main()
