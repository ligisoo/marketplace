"""
Tip Result Verification Service

Automatically verifies tip results by matching with livescore data
and determining if each bet won or lost based on the market.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from django.utils import timezone
from django.db.models import Q

logger = logging.getLogger(__name__)


class ResultVerifier:
    """
    Service to verify tip results using livescore data.
    """

    def __init__(self):
        from .livescore_scraper import LivescoreScraper
        self.livescore_scraper = LivescoreScraper()

    def verify_tips(self, date: str = None) -> Dict:
        """
        Verify all unverified tips for a given date.

        Args:
            date: Date in format 'YYYY-MM-DD' (default: today)

        Returns:
            Dictionary with verification statistics
        """
        from apps.tips.models import Tip, TipMatch

        # Get all active tips with unverified results
        tips_to_verify = Tip.objects.filter(
            status='active',
            is_resulted=False,
            expires_at__lt=timezone.now()  # Only verify expired tips
        ).prefetch_related('matches')

        logger.info(f"Found {tips_to_verify.count()} tips to verify")

        # Scrape livescore
        logger.info("Scraping livescore...")
        livescore_matches = self.livescore_scraper.scrape_live_scores_sync(date)
        logger.info(f"Scraped {len(livescore_matches)} matches from livescore")

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
                result = self._verify_tip(tip, livescore_matches)

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

    def _verify_tip(self, tip, livescore_matches: List[Dict]) -> Dict:
        """
        Verify a single tip by checking all its matches.

        Returns:
            Dictionary with verification result
        """
        from apps.tips.models import TipMatch

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
            # Find matching livescore match
            livescore_match = self.livescore_scraper.match_teams(
                tip_match.home_team,
                tip_match.away_team,
                livescore_matches
            )

            if livescore_match:
                # Check if match is finished
                if not livescore_match['is_finished']:
                    logger.info(f"Match {tip_match.home_team} vs {tip_match.away_team} not yet finished")
                    continue

                # Verify this specific match
                match_won = self._check_market_result(
                    tip_match.market,
                    tip_match.selection,
                    livescore_match['home_score'],
                    livescore_match['away_score']
                )

                # Update tip match
                tip_match.is_resulted = True
                tip_match.is_won = match_won
                tip_match.actual_result = f"{livescore_match['home_score']}-{livescore_match['away_score']}"
                tip_match.save()

                verified_matches += 1
                if match_won:
                    won_matches += 1

                logger.info(
                    f"Match verified: {tip_match.home_team} vs {tip_match.away_team} "
                    f"Result: {livescore_match['home_score']}-{livescore_match['away_score']} "
                    f"Market: {tip_match.market} Selection: {tip_match.selection} "
                    f"Won: {match_won}"
                )
            else:
                not_found_matches += 1
                logger.warning(
                    f"No livescore match found for: {tip_match.home_team} vs {tip_match.away_team}"
                )

        # Determine overall tip result
        if verified_matches == total_matches:
            # All matches verified
            tip_won = (won_matches == total_matches)  # All must win for betslip to win

            tip.is_resulted = True
            tip.is_won = tip_won
            tip.result_verified_at = timezone.now()
            tip.save()

            logger.info(
                f"Tip {tip.id} verified: "
                f"Won {won_matches}/{total_matches} matches - "
                f"Betslip {'WON' if tip_won else 'LOST'}"
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

    def _check_market_result(self, market: str, selection: str, home_score: int, away_score: int) -> bool:
        """
        Check if a bet won based on market type, selection, and final score.

        Args:
            market: Betting market (e.g., "Over 2.5", "1X2", "BTTS")
            selection: The bet selection (e.g., "Over", "1", "Yes")
            home_score: Final home team score
            away_score: Final away team score

        Returns:
            True if bet won, False if lost
        """
        if home_score is None or away_score is None:
            return False

        market_lower = market.lower().strip()
        selection_lower = selection.lower().strip()

        total_goals = home_score + away_score

        # Over/Under Goals
        if 'over' in market_lower or 'under' in market_lower:
            # Extract goal line (e.g., "2.5", "1.5", "3.5")
            goal_line = self._extract_goal_line(market)

            if goal_line:
                if 'over' in selection_lower:
                    return total_goals > goal_line
                elif 'under' in selection_lower:
                    return total_goals < goal_line

        # 1X2 / Match Result
        if '1x2' in market_lower or 'match result' in market_lower or 'full time result' in market_lower:
            if '1' in selection or 'home' in selection_lower:
                return home_score > away_score
            elif 'x' in selection_lower or 'draw' in selection_lower:
                return home_score == away_score
            elif '2' in selection or 'away' in selection_lower:
                return away_score > home_score

        # Both Teams to Score (BTTS/GG)
        if 'both teams' in market_lower or 'btts' in market_lower or 'gg' in market_lower:
            both_scored = (home_score > 0 and away_score > 0)

            if 'yes' in selection_lower or 'gg' in selection_lower:
                return both_scored
            elif 'no' in selection_lower or 'ng' in selection_lower:
                return not both_scored

        # Double Chance
        if 'double chance' in market_lower:
            if '1x' in selection_lower or 'home or draw' in selection_lower:
                return home_score >= away_score
            elif 'x2' in selection_lower or 'away or draw' in selection_lower:
                return away_score >= home_score
            elif '12' in selection_lower or 'home or away' in selection_lower:
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
                if 'home' in selection_lower or selection.startswith(str(home_score)[0]):
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
