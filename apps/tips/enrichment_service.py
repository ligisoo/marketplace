"""
Service to enrich betslip data with accurate match information from API-Football
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from fuzzywuzzy import fuzz
from django.db.models import Q

from apps.fixtures.models import Fixture, Team
from apps.fixtures.services import APIFootballService
from .models import TipMatch

logger = logging.getLogger(__name__)


class DataEnrichmentService:
    """Service to enrich scraped betslip data with API-Football data"""

    def __init__(self):
        self.api_service = APIFootballService()
        self.match_threshold = 75  # Minimum similarity score for team matching

    def _normalize_team_name(self, team_name: str) -> str:
        """Normalize team name for better matching"""
        if not team_name:
            return ""

        # Common abbreviations and variations
        replacements = {
            'Man Utd': 'Manchester United',
            'Man United': 'Manchester United',
            'Man City': 'Manchester City',
            'Spurs': 'Tottenham',
            'Tottenham Hotspur': 'Tottenham',
            'Newcastle': 'Newcastle United',
            'West Ham': 'West Ham United',
            'Leicester': 'Leicester City',
            'Brighton': 'Brighton & Hove Albion',
            'Wolves': 'Wolverhampton Wanderers',
            'Nottm Forest': 'Nottingham Forest',
        }

        normalized = team_name.strip()

        # Check for direct replacements
        for abbr, full in replacements.items():
            if abbr.lower() == normalized.lower():
                normalized = full
                break

        # Remove common suffixes
        suffixes = ['FC', 'AFC', 'CF', 'United', 'City', 'Town', 'Rovers', 'Wanderers']
        words = normalized.split()
        if len(words) > 1 and words[-1] in suffixes:
            # Keep the suffix for disambiguation (e.g., Manchester United vs Manchester City)
            pass

        return normalized.strip()

    def _calculate_team_similarity(self, team1: str, team2: str) -> int:
        """Calculate similarity score between two team names"""
        # Normalize both names
        norm1 = self._normalize_team_name(team1)
        norm2 = self._normalize_team_name(team2)

        # Use multiple fuzzy matching algorithms
        ratio = fuzz.ratio(norm1.lower(), norm2.lower())
        partial_ratio = fuzz.partial_ratio(norm1.lower(), norm2.lower())
        token_sort_ratio = fuzz.token_sort_ratio(norm1.lower(), norm2.lower())

        # Return the best score
        return max(ratio, partial_ratio, token_sort_ratio)

    def find_matching_fixture(
        self,
        home_team: str,
        away_team: str,
        match_date: Optional[datetime] = None
    ) -> Optional[Fixture]:
        """
        Find the matching fixture from API-Football data

        Args:
            home_team: Home team name from scraped data
            away_team: Away team name from scraped data
            match_date: Optional match date to narrow search

        Returns:
            Fixture object if found, None otherwise
        """
        # Determine search date range
        if match_date:
            # Search +/- 2 days from the given date to handle timezone differences
            # and cases where the default "tomorrow" date was used
            start_date = match_date.date() - timedelta(days=2)
            end_date = match_date.date() + timedelta(days=3)
        else:
            # Search upcoming fixtures (next 7 days)
            start_date = datetime.now().date()
            end_date = start_date + timedelta(days=7)

        # Get fixtures in date range
        fixtures = Fixture.objects.filter(
            date__date__gte=start_date,
            date__date__lt=end_date
        ).select_related('home_team', 'away_team', 'league')

        best_match = None
        best_score = 0

        for fixture in fixtures:
            # Calculate similarity for both teams
            home_similarity = self._calculate_team_similarity(
                home_team,
                fixture.home_team.name
            )
            away_similarity = self._calculate_team_similarity(
                away_team,
                fixture.away_team.name
            )

            # Average similarity score
            avg_score = (home_similarity + away_similarity) / 2

            # Both teams must meet threshold individually
            if (home_similarity >= self.match_threshold and
                away_similarity >= self.match_threshold and
                avg_score > best_score):
                best_score = avg_score
                best_match = fixture

        if best_match:
            logger.info(
                f"Matched '{home_team} vs {away_team}' to "
                f"'{best_match.home_team.name} vs {best_match.away_team.name}' "
                f"(score: {best_score:.1f})"
            )
        else:
            logger.warning(
                f"No match found for '{home_team} vs {away_team}' "
                f"in date range {start_date} to {end_date}"
            )

        return best_match

    def enrich_tip_match(self, tip_match: TipMatch) -> bool:
        """
        Enrich a single TipMatch with API-Football data

        Args:
            tip_match: TipMatch instance to enrich

        Returns:
            bool: True if successfully enriched, False otherwise
        """
        try:
            # Find matching fixture
            fixture = self.find_matching_fixture(
                tip_match.home_team,
                tip_match.away_team,
                tip_match.match_date
            )

            if not fixture:
                return False

            # Update TipMatch with fixture data
            tip_match.api_match_id = str(fixture.api_id)
            tip_match.league = fixture.league.name
            tip_match.match_date = fixture.date

            # Update team names to official names
            tip_match.home_team = fixture.home_team.name
            tip_match.away_team = fixture.away_team.name

            # Update results if available
            if fixture.is_finished:
                tip_match.is_resulted = True
                result_str = fixture.get_result_string()
                tip_match.actual_result = result_str

                # Determine if bet won (simplified logic)
                # This would need to be expanded based on market type
                # For now, just mark as resulted
                # TODO: Implement market-specific result checking

            tip_match.save()

            logger.info(
                f"Enriched TipMatch {tip_match.id} with fixture {fixture.api_id}"
            )

            return True

        except Exception as e:
            logger.error(
                f"Error enriching TipMatch {tip_match.id}: {str(e)}",
                exc_info=True
            )
            return False

    def enrich_tip_matches(self, tip_matches: List[TipMatch]) -> Dict[str, int]:
        """
        Enrich multiple TipMatches with API-Football data

        Args:
            tip_matches: List of TipMatch instances

        Returns:
            dict: Statistics about enrichment process
        """
        stats = {
            'total': len(tip_matches),
            'enriched': 0,
            'failed': 0,
            'already_enriched': 0
        }

        for tip_match in tip_matches:
            # Skip if already has API match ID
            if tip_match.api_match_id:
                stats['already_enriched'] += 1
                continue

            # Attempt enrichment
            if self.enrich_tip_match(tip_match):
                stats['enriched'] += 1
            else:
                stats['failed'] += 1

        logger.info(f"Enrichment complete: {stats}")
        return stats

    def fetch_and_enrich(
        self,
        tip_matches: List[TipMatch],
        fetch_fixtures: bool = True
    ) -> Dict[str, int]:
        """
        Fetch latest fixtures from API and enrich tip matches

        Args:
            tip_matches: List of TipMatch instances
            fetch_fixtures: Whether to fetch new fixtures from API first

        Returns:
            dict: Statistics about enrichment process
        """
        if fetch_fixtures:
            # Fetch upcoming fixtures for next 7 days
            for days_ahead in range(7):
                date = datetime.now().date() + timedelta(days=days_ahead)

                # Check if we can make request
                if not self.api_service._can_make_request():
                    logger.warning(
                        f"API limit reached, stopping fixture fetch at day {days_ahead}"
                    )
                    break

                # Fetch and save fixtures
                response = self.api_service.fetch_fixtures(date=date)
                if response:
                    created, updated = self.api_service.save_fixtures(response)
                    logger.info(
                        f"Fetched fixtures for {date}: "
                        f"{created} created, {updated} updated"
                    )

        # Enrich tip matches
        return self.enrich_tip_matches(tip_matches)
