"""
Tip Result Verification Service

Automatically verifies tip results by matching with API-Football fixture data
and determining if each bet won or lost based on the market.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class ResultVerifier:
    """
    Service to verify tip results using API-Football data.
    """

    def __init__(self):
        from apps.fixtures.models import Fixture
        from apps.fixtures.services import APIFootballService
        self.api_service = APIFootballService()

    def verify_tips(self, date: str = None, fetch_from_api: bool = False) -> Dict:
        """
        Verify all unverified tips for a given date.

        Args:
            date: Date in format 'YYYY-MM-DD' (default: today)
            fetch_from_api: Whether to fetch fresh fixtures from API (default: False, use DB only)

        Returns:
            Dictionary with verification statistics
        """
        from apps.tips.models import Tip, TipMatch
        from apps.fixtures.models import Fixture

        # Get all active tips with unverified results
        tips_to_verify = Tip.objects.filter(
            status='active',
            is_resulted=False
        ).prefetch_related('matches')

        logger.info(f"Found {tips_to_verify.count()} tips to verify")

        # Optionally fetch fresh fixtures from API
        if fetch_from_api:
            # Fetch fixtures for today and yesterday (to catch late finishes)
            if date:
                dates_to_fetch = [datetime.strptime(date, '%Y-%m-%d').date()]
            else:
                today = datetime.now().date()
                dates_to_fetch = [today, today - timedelta(days=1)]

            for fetch_date in dates_to_fetch:
                if self.api_service._can_make_request():
                    logger.info(f"Fetching fixtures from API for {fetch_date}")
                    response = self.api_service.fetch_fixtures(date=fetch_date)
                    if response:
                        created, updated = self.api_service.save_fixtures(response)
                        logger.info(f"API fetch: {created} created, {updated} updated")
                else:
                    logger.warning("API limit reached, using database fixtures only")
                    break

        stats = {
            'tips_checked': 0,
            'tips_verified': 0,
            'tips_won': 0,
            'tips_lost': 0,
            'tips_pending': 0,
            'matches_verified': 0,
            'matches_not_found': 0
        }

        for tip in tips_to_verify:
            stats['tips_checked'] += 1

            try:
                result = self._verify_tip(tip)

                if result['status'] == 'verified':
                    stats['tips_verified'] += 1
                    if result['is_won']:
                        stats['tips_won'] += 1
                    else:
                        stats['tips_lost'] += 1

                    stats['matches_verified'] += result['matches_verified']
                    stats['matches_not_found'] += result['matches_not_found']

                elif result['status'] == 'pending':
                    stats['tips_pending'] += 1
                    stats['matches_not_found'] += result['matches_not_found']

            except Exception as e:
                logger.error(f"Error verifying tip {tip.id}: {str(e)}", exc_info=True)
                continue

        return stats

    def _verify_tip(self, tip) -> Dict:
        """
        Verify a single tip by checking all its matches against API-Football data.

        Returns:
            Dictionary with verification result
        """
        from apps.tips.models import TipMatch
        from apps.fixtures.models import Fixture

        matches = tip.matches.all()
        total_matches = matches.count()

        if total_matches == 0:
            return {
                'status': 'no_matches',
                'is_won': False,
                'matches_verified': 0,
                'matches_not_found': 0
            }

        verified_matches = 0
        won_matches = 0
        not_found_matches = 0

        for tip_match in matches:
            # If already resulted, use existing result
            if tip_match.is_resulted:
                verified_matches += 1
                if tip_match.is_won:
                    won_matches += 1
                continue

            # Try to find fixture by api_match_id first (if enriched)
            fixture = None

            if tip_match.api_match_id:
                try:
                    fixture = Fixture.objects.get(api_id=int(tip_match.api_match_id))
                except (Fixture.DoesNotExist, ValueError):
                    logger.warning(f"Fixture with api_id {tip_match.api_match_id} not found")

            # If not found by API ID, try fuzzy matching
            if not fixture:
                fixture = self._find_matching_fixture(tip_match)

            if fixture:
                # Save api_match_id early so we can track live scores
                if not tip_match.api_match_id:
                    tip_match.api_match_id = str(fixture.api_id)
                    tip_match.save(update_fields=['api_match_id'])
                    
                # Check if match is finished or concluded (postponed, cancelled, abandoned, etc.)
                is_concluded = fixture.is_finished or fixture.status_short in ['PST', 'CANC', 'ABD', 'AWD', 'WO']
                if not is_concluded:
                    logger.info(f"Match {tip_match.home_team} vs {tip_match.away_team} not yet finished (Status: {fixture.status_short})")
                    continue

                # Check if the match is voided (postponed, cancelled, abandoned, etc.)
                is_void = fixture.status_short in ['PST', 'CANC', 'ABD', 'AWD', 'WO']
                match_won = False

                if not is_void:
                    # Verify this specific match
                    match_result = self._check_market_result(
                        tip_match.market,
                        tip_match.selection,
                        fixture.home_goals,
                        fixture.away_goals,
                        home_team=tip_match.home_team,
                        away_team=tip_match.away_team
                    )
                    
                    if match_result == 'void':
                        is_void = True
                    else:
                        match_won = bool(match_result)

                # Update tip match
                tip_match.is_resulted = True
                if is_void:
                    from decimal import Decimal
                    tip_match.is_won = True  # Treat void as won so accumulator continues
                    tip_match.actual_result = f"Void / Push ({fixture.status_short})"
                    tip_match.odds = Decimal('1.00')  # Reset odds to 1.0
                else:
                    tip_match.is_won = match_won
                    tip_match.actual_result = fixture.get_result_string()
                
                tip_match.save()

                verified_matches += 1
                if tip_match.is_won:
                    won_matches += 1

                logger.info(
                    f"Match verified: {tip_match.home_team} vs {tip_match.away_team} "
                    f"Result: {fixture.home_goals}-{fixture.away_goals} "
                    f"Market: {tip_match.market} Selection: {tip_match.selection} "
                    f"Won: {tip_match.is_won} (Void: {is_void})"
                )
            else:
                # Try fallback via livescore.cz scraper for matches absent from API-Football
                livescore_verified = self._verify_via_livescore_cz(tip_match)
                if livescore_verified:
                    verified_matches += 1
                    if tip_match.is_won:
                        won_matches += 1
                else:
                    not_found_matches += 1
                    logger.warning(
                        f"No fixture found in API-Football or livescore.cz for: {tip_match.home_team} vs {tip_match.away_team}"
                    )


        # Determine overall tip result
        if verified_matches == total_matches:
            # All matches verified
            tip_won = (won_matches == total_matches)  # All must win for betslip to win

            tip.is_resulted = True
            tip.is_won = tip_won
            tip.result_verified_at = timezone.now()
            tip.status = 'archived'  # Mark as archived after verification
            
            # Recalculate tip odds in case of any voided matches
            from decimal import Decimal
            total_odds = Decimal('1.00')
            for m in tip.matches.all():
                total_odds *= m.odds
            tip.odds = round(total_odds, 2)
            
            tip.save()

            logger.info(
                f"Tip {tip.id} verified: "
                f"Won {won_matches}/{total_matches} matches - "
                f"Betslip {'WON' if tip_won else 'LOST'} - New Odds: {tip.odds}"
            )

            return {
                'status': 'verified',
                'is_won': tip_won,
                'matches_verified': verified_matches,
                'matches_not_found': not_found_matches
            }
        else:
            # Not all matches verified yet
            return {
                'status': 'pending',
                'is_won': False,
                'matches_verified': verified_matches,
                'matches_not_found': not_found_matches
            }

    def _find_matching_fixture(self, tip_match) -> Optional['Fixture']:
        """
        Find matching fixture using fuzzy team name matching

        Args:
            tip_match: TipMatch instance

        Returns:
            Fixture if found, None otherwise
        """
        try:
            from fuzzywuzzy import fuzz
            calc_ratio = fuzz.ratio
        except ImportError:
            from difflib import SequenceMatcher
            def calc_ratio(s1: str, s2: str) -> float:
                return SequenceMatcher(None, s1, s2).ratio() * 100

        from apps.fixtures.models import Fixture
        from datetime import timedelta

        match_date = tip_match.match_date.date()
        fixtures = Fixture.objects.filter(
            date__date__range=[
                match_date - timedelta(days=1),
                match_date + timedelta(days=1)
            ]
        )

        def is_team_match(name1: str, name2: str) -> Tuple[bool, float]:
            n1 = name1.lower().strip()
            n2 = name2.lower().strip()
            if n1 == n2:
                return True, 100.0
            
            # Substring match (ensure at least 4 characters to avoid false matches on 'fc', 'utd', etc.)
            if len(n1) >= 4 and n1 in n2:
                return True, 90.0
            if len(n2) >= 4 and n2 in n1:
                return True, 90.0
                
            # Fuzzy match
            ratio = calc_ratio(n1, n2)
            if ratio >= 75:
                return True, ratio
            return False, ratio

        best_match = None
        best_score = 0

        for fixture in fixtures:
            home_matched, home_score = is_team_match(tip_match.home_team, fixture.home_team.name)
            away_matched, away_score = is_team_match(tip_match.away_team, fixture.away_team.name)

            if home_matched and away_matched:
                avg_score = (home_score + away_score) / 2
                if avg_score > best_score:
                    best_score = avg_score
                    best_match = fixture

        if best_match:
            logger.info(
                f"Fuzzy matched '{tip_match.home_team} vs {tip_match.away_team}' to "
                f"'{best_match.home_team.name} vs {best_match.away_team.name}' (score: {best_score:.1f})"
            )

        return best_match

    def _check_market_result(self, market: str, selection: str, home_score: int, away_score: int, home_team: str = "", away_team: str = ""):
        """
        Check if a bet won based on market type, selection, and final score.

        Args:
            market: Betting market (e.g., "Over 2.5", "1X2", "BTTS")
            selection: The bet selection (e.g., "Over", "1", "Yes")
            home_score: Final home team score
            away_score: Final away team score
            home_team: Home team name
            away_team: Away team name

        Returns:
            True if bet won, False if lost, 'void' if bet is push/voided
        """
        if home_score is None or away_score is None:
            return False

        market_lower = market.lower().strip()
        selection_lower = selection.lower().strip()

        total_goals = home_score + away_score

        # Over/Under Goals (including "Total Goals" market)
        if ('over' in market_lower or 'under' in market_lower or 
            'total goals' in market_lower or 'goals total' in market_lower):
            
            # Extract goal line from market or selection
            goal_line = self._extract_goal_line(market)
            if not goal_line:
                goal_line = self._extract_goal_line(selection)

            if goal_line:
                is_over = False
                is_under = False
                
                if 'over' in selection_lower or '+' in selection_lower or '>' in selection_lower:
                    is_over = True
                elif 'under' in selection_lower or '-' in selection_lower or '<' in selection_lower:
                    is_under = True
                elif 'yes' in selection_lower:
                    if 'over' in market_lower:
                        is_over = True
                    elif 'under' in market_lower:
                        is_under = True
                elif 'no' in selection_lower:
                    if 'over' in market_lower:
                        is_under = True
                    elif 'under' in market_lower:
                        is_over = True
                else:
                    if 'over' in market_lower:
                        is_over = True
                    elif 'under' in market_lower:
                        is_under = True
                
                if is_over:
                    return total_goals > goal_line
                elif is_under:
                    return total_goals < goal_line

        # 1X2 / Match Result
        if '1x2' in market_lower or 'match result' in market_lower or 'full time result' in market_lower or '3 way' in market_lower:
            # Check team names first if provided
            if home_team and away_team:
                h_name = home_team.lower().strip()
                a_name = away_team.lower().strip()
                # Check for exact or substring match of team names in selection
                if selection_lower == h_name or (len(h_name) > 3 and h_name in selection_lower) or (len(selection_lower) > 3 and selection_lower in h_name):
                    return home_score > away_score
                elif selection_lower == a_name or (len(a_name) > 3 and a_name in selection_lower) or (len(selection_lower) > 3 and selection_lower in a_name):
                    return away_score > home_score

            if selection_lower in ['1x', 'home/draw', 'home or draw']:
                return home_score >= away_score
            elif selection_lower in ['x2', 'draw/away', 'away or draw']:
                return away_score >= home_score
            elif selection_lower in ['12', 'home/away', 'home or away']:
                return home_score != away_score
            elif selection_lower in ['1', 'home'] or selection.strip() == '1':
                return home_score > away_score
            elif selection_lower in ['x', 'draw'] or selection.strip().upper() == 'X':
                return home_score == away_score
            elif selection_lower in ['2', 'away'] or selection.strip() == '2':
                return away_score > home_score

        # Draw No Bet (DNB)
        if 'draw no bet' in market_lower or 'dnb' in market_lower:
            if home_score == away_score:
                return 'void'
            
            if home_team and away_team:
                h_name = home_team.lower().strip()
                a_name = away_team.lower().strip()
                if selection_lower == h_name or (len(h_name) > 3 and h_name in selection_lower) or (len(selection_lower) > 3 and selection_lower in h_name):
                    return home_score > away_score
                elif selection_lower == a_name or (len(a_name) > 3 and a_name in selection_lower) or (len(selection_lower) > 3 and selection_lower in a_name):
                    return away_score > home_score

            if selection_lower in ['1', 'home'] or selection.strip() == '1':
                return home_score > away_score
            elif selection_lower in ['2', 'away'] or selection.strip() == '2':
                return away_score > home_score

        # Both Teams to Score (BTTS/GG)
        if 'both teams' in market_lower or 'btts' in market_lower or 'gg' in market_lower:
            both_scored = (home_score > 0 and away_score > 0)

            if 'yes' in selection_lower or 'gg' in selection_lower or selection_lower == '1' or selection_lower == 'y':
                return both_scored
            elif 'no' in selection_lower or 'ng' in selection_lower or selection_lower == '2' or selection_lower == 'n':
                return not both_scored

        # Double Chance
        if 'double chance' in market_lower:
            # Check team names first if provided
            if home_team and away_team:
                h_name = home_team.lower().strip()
                a_name = away_team.lower().strip()
                if h_name in selection_lower and ('draw' in selection_lower or 'x' in selection_lower or '1' in selection_lower):
                    return home_score >= away_score
                elif a_name in selection_lower and ('draw' in selection_lower or 'x' in selection_lower or '2' in selection_lower):
                    return away_score >= home_score
                elif h_name in selection_lower and a_name in selection_lower:
                    return home_score != away_score

            if '1x' in selection_lower or 'home or draw' in selection_lower or 'home/draw' in selection_lower or '1 or x' in selection_lower or 'draw or home' in selection_lower:
                return home_score >= away_score
            elif 'x2' in selection_lower or 'away or draw' in selection_lower or 'draw/away' in selection_lower or 'x or 2' in selection_lower or '2 or x' in selection_lower:
                return away_score >= home_score
            elif '12' in selection_lower or 'home or away' in selection_lower or 'home/away' in selection_lower or '1 or 2' in selection_lower or 'away or home' in selection_lower:
                return home_score != away_score

        # Correct Score
        if 'correct score' in market_lower:
            # Extract score from selection (e.g., "2-1", "0:0")
            predicted_score = self._extract_score(selection)
            if predicted_score:
                return (predicted_score[0] == home_score and predicted_score[1] == away_score)

        # Asian Handicap
        if 'asian handicap' in market_lower or 'handicap' in market_lower:
            handicap = self._extract_handicap(selection)
            if handicap is not None:
                # Determine which team has handicap
                is_home_handicap = False
                if home_team and home_team.lower().strip() in selection_lower:
                    is_home_handicap = True
                elif away_team and away_team.lower().strip() in selection_lower:
                    is_home_handicap = False
                elif 'home' in selection_lower or '1' in selection_lower:
                    is_home_handicap = True
                
                if is_home_handicap:
                    adjusted_home = home_score + handicap
                    return adjusted_home > away_score
                else:
                    adjusted_away = away_score + handicap
                    return adjusted_away > home_score

        # If we can't determine, log it and return False
        logger.warning(
            f"Unknown market type: {market} with selection: {selection}. "
            f"Score: {home_score}-{away_score}"
        )
        return False

    def _extract_goal_line(self, market: str) -> Optional[float]:
        """Extract goal line from market string (e.g., "Over 2.5" -> 2.5)"""
        match = re.search(r'(\d+\.?\d*)', market)
        if match:
            return float(match.group(1))
        return None

    def _extract_score(self, selection: str) -> Optional[Tuple[int, int]]:
        """Extract score from selection string (e.g., "2-1" -> (2, 1))"""
        match = re.search(r'(\d+)[:-](\d+)', selection)
        if match:
            return (int(match.group(1)), int(match.group(2)))
        return None

    def _extract_handicap(self, selection: str) -> Optional[float]:
        """Extract handicap value from selection (e.g., "[+0.50]" -> 0.5)"""
        match = re.search(r'([+-]?\d+\.?\d*)', selection)
        if match:
            return float(match.group(1))
        return None

    def _verify_via_livescore_cz(self, tip_match) -> bool:
        """
        Fallback verification for matches absent from API-Football.
        Scrapes livescore.cz for finished matches and attempts fuzzy team matching.
        """
        try:
            from .livescore_cz_scraper import LivescoreCzScraper
        except ImportError:
            logger.error("Could not import LivescoreCzScraper")
            return False

        try:
            from fuzzywuzzy import fuzz
            calc_ratio = fuzz.ratio
        except ImportError:
            from difflib import SequenceMatcher
            def calc_ratio(s1: str, s2: str) -> float:
                return SequenceMatcher(None, s1, s2).ratio() * 100

        scraper = LivescoreCzScraper()
        # Fetch finished games for the tip_match's date
        from django.utils import timezone
        today = timezone.now().date()
        match_date = tip_match.match_date.date()
        offset = (match_date - today).days
        
        scraped_matches = scraper.fetch_scores(day_offset=offset, status_filter='finished')
        
        home_tip = tip_match.home_team.lower().strip()
        away_tip = tip_match.away_team.lower().strip()

        for m in scraped_matches:
            home_scraped = m['home_team'].lower().strip()
            away_scraped = m['away_team'].lower().strip()

            # Check fuzzy team matching
            home_ratio = calc_ratio(home_tip, home_scraped)
            away_ratio = calc_ratio(away_tip, away_scraped)

            # Substring match support
            if len(home_tip) >= 4 and (home_tip in home_scraped or home_scraped in home_tip):
                home_ratio = max(home_ratio, 90.0)
            if len(away_tip) >= 4 and (away_tip in away_scraped or away_scraped in away_tip):
                away_ratio = max(away_ratio, 90.0)

            if home_ratio >= 75 and away_ratio >= 75 and m['status'] == 'finished':
                if m['home_goals'] is None or m['away_goals'] is None:
                    continue

                match_result = self._check_market_result(
                    tip_match.market,
                    tip_match.selection,
                    m['home_goals'],
                    m['away_goals'],
                    home_team=tip_match.home_team,
                    away_team=tip_match.away_team
                )
                
                tip_match.is_resulted = True
                if match_result == 'void':
                    from decimal import Decimal
                    tip_match.is_won = True
                    tip_match.actual_result = f"Void / Push ({m['score']})"
                    tip_match.odds = Decimal('1.00')
                else:
                    tip_match.is_won = bool(match_result)
                    tip_match.actual_result = f"{m['home_goals']}-{m['away_goals']} (livescore.cz)"
                
                tip_match.save()
                logger.info(
                    f"Match verified via livescore.cz: {tip_match.home_team} vs {tip_match.away_team} "
                    f"Result: {m['home_goals']}-{m['away_goals']} Won: {tip_match.is_won}"
                )
                return True

        return False

