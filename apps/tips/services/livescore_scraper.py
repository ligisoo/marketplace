"""
Livescore Scraper Service

Scrapes live match scores from livescore.com to automatically verify tip results.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from django.utils import timezone
from fuzzywuzzy import fuzz

logger = logging.getLogger(__name__)


class LivescoreScraper:
    """
    Scraper for livescore.com to get match results and verify tips.
    """

    def __init__(self):
        self.base_url = "https://www.livescore.com/en/football"

    async def scrape_live_scores(self, date: str = None) -> List[Dict]:
        """
        Scrape live and finished scores from livescore.com

        Args:
            date: Date in format 'YYYY-MM-DD' (default: today)

        Returns:
            List of match dictionaries with scores
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            logger.error("Playwright not installed")
            return []

        if not date:
            date = timezone.now().strftime('%Y-%m-%d')

        url = f"{self.base_url}/{date}/" if date != timezone.now().strftime('%Y-%m-%d') else f"{self.base_url}/live/"

        matches = []

        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()

                try:
                    logger.info(f"Scraping livescore from: {url}")
                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)

                    # Wait for matches to load
                    await asyncio.sleep(5)

                    # Find all match containers
                    match_elements = await page.query_selector_all('[data-id*="_mtc-r"]')
                    logger.info(f"Found {len(match_elements)} matches")

                    for match_elem in match_elements:
                        try:
                            match_data = await self._extract_match_data(match_elem)
                            if match_data:
                                matches.append(match_data)
                        except Exception as e:
                            logger.error(f"Error extracting match: {str(e)}")
                            continue

                except Exception as e:
                    logger.error(f"Error scraping livescore: {str(e)}")
                finally:
                    await browser.close()

        except Exception as e:
            # Handle Playwright browser not installed or other launch errors
            error_msg = str(e)
            if "Executable doesn't exist" in error_msg or "ms-playwright" in error_msg:
                logger.error(
                    "Playwright browsers not installed. "
                    "Run 'playwright install chromium' to fix. "
                    "Skipping livescore scraping for this run."
                )
            else:
                logger.error(f"Failed to launch browser: {error_msg}")

        return matches

    async def _extract_match_data(self, match_element) -> Optional[Dict]:
        """Extract data from a single match element"""
        try:
            # Get match ID from data-id attribute
            data_id = await match_element.get_attribute('data-id')
            if not data_id:
                return None

            # Extract match ID (e.g., "0-1547645_mtc-r_live" -> "1547645")
            match_id = data_id.split('_')[0].split('-')[-1]

            # Extract team names
            home_team_elem = await match_element.query_selector(f'[data-id*="_hm-tm-nm"]')
            away_team_elem = await match_element.query_selector(f'[data-id*="_aw-tm-nm"]')

            home_team = await home_team_elem.inner_text() if home_team_elem else None
            away_team = await away_team_elem.inner_text() if away_team_elem else None

            if not home_team or not away_team:
                return None

            # Extract scores
            home_score_elem = await match_element.query_selector(f'[data-id="{match_id}_hm-sc"]')
            away_score_elem = await match_element.query_selector(f'[data-id="{match_id}_aw-sc"]')

            home_score = await home_score_elem.inner_text() if home_score_elem else None
            away_score = await away_score_elem.inner_text() if away_score_elem else None

            # Extract match status/time
            status_elem = await match_element.query_selector('[data-id*="_st-tm"]')
            status = await status_elem.inner_text() if status_elem else None

            # Determine if match is finished
            is_finished = status and ('FT' in status or status == '90+' or 'AET' in status or 'Pen' in status)

            match_data = {
                'match_id': match_id,
                'home_team': home_team.strip(),
                'away_team': away_team.strip(),
                'home_score': int(home_score) if home_score and home_score.isdigit() else None,
                'away_score': int(away_score) if away_score and away_score.isdigit() else None,
                'status': status.strip() if status else 'Unknown',
                'is_finished': is_finished,
                'scraped_at': timezone.now().isoformat()
            }

            return match_data

        except Exception as e:
            logger.error(f"Error extracting match data: {str(e)}")
            return None

    def match_teams(self, tip_home: str, tip_away: str, livescore_matches: List[Dict]) -> Optional[Dict]:
        """
        Find a match in livescore data that matches the tip teams using fuzzy matching.

        Args:
            tip_home: Home team from tip
            tip_away: Away team from tip
            livescore_matches: List of matches from livescore

        Returns:
            Matching livescore match or None
        """
        best_match = None
        best_score = 0

        for match in livescore_matches:
            # Calculate similarity for both teams
            home_similarity = self._team_similarity(tip_home, match['home_team'])
            away_similarity = self._team_similarity(tip_away, match['away_team'])

            # Average similarity
            total_score = (home_similarity + away_similarity) / 2

            # Only consider if both teams have reasonable similarity
            if home_similarity > 60 and away_similarity > 60 and total_score > best_score:
                best_score = total_score
                best_match = match

        # Only return if similarity is high enough
        if best_match and best_score > 70:
            best_match['match_confidence'] = best_score
            return best_match

        return None

    def _team_similarity(self, team1: str, team2: str) -> float:
        """
        Calculate similarity between two team names.
        Handles common variations and abbreviations.
        """
        if not team1 or not team2:
            return 0.0

        # Normalize
        t1 = self._normalize_team_name(team1)
        t2 = self._normalize_team_name(team2)

        # Direct match
        if t1 == t2:
            return 100.0

        # Check if one contains the other
        if t1 in t2 or t2 in t1:
            return 90.0

        # Fuzzy match
        return fuzz.ratio(t1, t2)

    def _normalize_team_name(self, name: str) -> str:
        """Normalize team name for comparison"""
        if not name:
            return ''

        normalized = name.lower().strip()

        # Handle common abbreviations (expand them first)
        abbreviations = {
            'man utd': 'manchester united',
            'man united': 'manchester united',
            'man city': 'manchester city',
            'man u': 'manchester united',
            'utd': 'united',
            'int': 'internacional',
            'inter': 'internacional',
        }

        for abbr, full in abbreviations.items():
            if abbr in normalized:
                normalized = normalized.replace(abbr, full)

        # Remove common suffixes after expansion
        suffixes = [' fc', ' afc', ' cf', ' united', ' city', ' town', ' wanderers']
        for suffix in suffixes:
            if normalized.endswith(suffix):
                normalized = normalized[:-len(suffix)].strip()

        return normalized

    def scrape_live_scores_sync(self, date: str = None) -> List[Dict]:
        """
        Synchronous wrapper for scraping live scores.
        Use this from Django views/management commands.
        """
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            matches = loop.run_until_complete(self.scrape_live_scores(date))
            return matches
        finally:
            loop.close()
