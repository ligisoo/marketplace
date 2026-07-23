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
    matches_to_reverify = TipMatch.objects.filter(is_resulted=True)
    
    print(f"Scanning {matches_to_reverify.count()} resulted matches for corrections...")
    reverified_count = 0
    tips_updated = set()

    for match in matches_to_reverify:
        if not match.api_match_id:
            continue
            
        fixture = Fixture.objects.filter(api_id=int(match.api_match_id)).first()
        if fixture and fixture.is_finished:
            new_won = verifier._check_market_result(
                match.market,
                match.selection,
                fixture.home_goals,
                fixture.away_goals,
                home_team=match.home_team,
                away_team=match.away_team
            )
            
            if new_won != match.is_won:
                print(f"✓ Match {match.id} ({match.home_team} vs {match.away_team}): is_won corrected from {match.is_won} to {new_won}")
                match.is_won = new_won
                match.save(update_fields=['is_won'])
                reverified_count += 1
                tips_updated.add(match.tip)

    # Re-evaluate parent tips
    for tip in tips_updated:
        all_matches = tip.matches.all()
        # All matches must be marked won and resulted
        all_won = all(m.is_resulted and m.is_won for m in all_matches)
        
        if tip.is_won != all_won:
            print(f"✓ Parent Tip {tip.id} ({tip.bet_code}): is_won corrected from {tip.is_won} to {all_won}")
            tip.is_won = all_won
            tip.save(update_fields=['is_won'])

    print(f"Done! Corrected {reverified_count} matches across {len(tips_updated)} tips.")

if __name__ == '__main__':
    main()
