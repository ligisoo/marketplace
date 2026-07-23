"""
Service for interacting with the API-Football API with caching support
"""
import requests
from datetime import datetime, date as dt_date, timedelta
from django.conf import settings
from django.conf import settings
from django.core.cache import cache
from .models import League, Team, Venue, Fixture, APIUsageLog


class APIFootballService:
    """Service class to handle API-Football API requests with caching"""

    BASE_URL = "https://v3.football.api-sports.io"
    CACHE_TIMEOUT_UPCOMING = 86400  # 24 hours for upcoming fixtures
    CACHE_TIMEOUT_LIVE = 900  # 15 minutes for live matches
    CACHE_TIMEOUT_FINISHED = None  # Never expire finished matches

    def __init__(self):
        self.api_key = settings.API_FOOTBALL_KEY
        self.daily_limit = settings.API_FOOTBALL_DAILY_LIMIT
        self.headers = {
            'x-rapidapi-host': 'v3.football.api-sports.io',
            'x-rapidapi-key': self.api_key
        }

    def _get_cache_key(self, endpoint, params):
        """Generate cache key from endpoint and params"""
        param_str = '_'.join([f"{k}_{v}" for k, v in sorted(params.items())])
        return f"apifootball_{endpoint}_{param_str}"

    def _can_make_request(self):
        """Check if we can make another API request"""
        return APIUsageLog.can_make_request(self.daily_limit)

    def _log_request(self, endpoint, params, cached=False):
        """Log API request for tracking"""
        APIUsageLog.objects.create(
            endpoint=endpoint,
            request_params=params,
            response_cached=cached
        )

    def fetch_fixtures(self, date=None, use_cache=True, force_refresh=False):
        """
        Fetch fixtures for a specific date with caching support

        Args:
            date: Date string in format YYYY-MM-DD or date object. If None, uses today's date.
            use_cache: Whether to use cached data if available
            force_refresh: Force refresh from API even if cached

        Returns:
            dict: API response data or cached data
        """
        # Convert date to string if needed
        if isinstance(date, dt_date):
            date = date.strftime('%Y-%m-%d')
        elif date is None:
            date = datetime.now().strftime('%Y-%m-%d')

        params = {'date': date}
        cache_key = self._get_cache_key('fixtures', params)

        # Check cache first
        if use_cache and not force_refresh:
            cached_data = cache.get(cache_key)
            if cached_data:
                self._log_request('fixtures', params, cached=True)
                return cached_data

        # Check API limit
        if not self._can_make_request():
            # Try to return cached data even if expired
            cached_data = cache.get(cache_key)
            if cached_data:
                self._log_request('fixtures', params, cached=True)
                return cached_data
            else:
                print(f"WARNING: API limit reached and no cached data available for {date}")
                return None

        # Fetch from API
        url = f"{self.BASE_URL}/fixtures"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Check for API-specific errors (like rate limit exceeded)
            if 'errors' in data and data['errors']:
                error_msg = str(data['errors'])
                if 'request limit' in error_msg.lower():
                    print(f"API rate limit exceeded: {error_msg}")
                    return None
                else:
                    print(f"API error: {error_msg}")

            # Cache the response only if no errors
            cache.set(cache_key, data, self.CACHE_TIMEOUT_UPCOMING)
            self._log_request('fixtures', params, cached=False)

            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching fixtures: {e}")
            # Try to return cached data on error
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            return None

    def fetch_live_fixtures(self, use_cache=True):
        """
        Fetch currently live fixtures

        Args:
            use_cache: Whether to use cached data (shorter cache time)

        Returns:
            dict: API response data
        """
        params = {'live': 'all'}
        cache_key = self._get_cache_key('fixtures_live', params)

        # Check cache with shorter timeout
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                self._log_request('fixtures', params, cached=True)
                return cached_data

        # Check API limit
        if not self._can_make_request():
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data
            print("WARNING: API limit reached for live fixtures")
            return None

        # Fetch from API
        url = f"{self.BASE_URL}/fixtures"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()

            # Check for API-specific errors (like rate limit exceeded)
            if 'errors' in data and data['errors']:
                error_msg = str(data['errors'])
                if 'request limit' in error_msg.lower():
                    print(f"API rate limit exceeded for live fixtures: {error_msg}")
                    return None
                else:
                    print(f"API error in live fixtures: {error_msg}")

            # Cache with shorter timeout for live matches only if no errors
            cache.set(cache_key, data, self.CACHE_TIMEOUT_LIVE)
            self._log_request('fixtures', params, cached=False)

            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching live fixtures: {e}")
            return None

    def fetch_recent_finished_fixtures(self):
        """
        Fetch fixtures that finished in the last 2 hours to catch any that 
        dropped out of the live feed before we got their final status
        
        Returns:
            dict: API response data
        """
        from datetime import datetime, timedelta
        
        # Get fixtures from 2 hours ago to now that are finished
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=2)
        
        params = {
            'from': start_time.strftime('%Y-%m-%d'),
            'to': end_time.strftime('%Y-%m-%d'),
            'status': 'FT'  # Only finished matches
        }
        
        if not self._can_make_request():
            print("WARNING: API limit reached for recent finished fixtures")
            return None
            
        url = f"{self.BASE_URL}/fixtures"
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            self._log_request('fixtures_recent_finished', params, cached=False)
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching recent finished fixtures: {e}")
            return None

    def enhanced_live_fixtures_update(self):
        """
        Enhanced live fixtures update that also checks for recently finished matches
        
        Returns:
            dict: Combined statistics from live and recent finished updates
        """
        stats = {
            'live_fixtures_created': 0,
            'live_fixtures_updated': 0,
            'recent_finished_created': 0,
            'recent_finished_updated': 0,
            'api_requests_used': 0,
            'errors': []
        }
        
        # Fetch live fixtures
        try:
            live_data = self.fetch_live_fixtures()
            if live_data:
                created, updated = self.save_fixtures(live_data)
                stats['live_fixtures_created'] = created
                stats['live_fixtures_updated'] = updated
                stats['api_requests_used'] += 1
        except Exception as e:
            stats['errors'].append(f"Live fixtures error: {e}")
        
        # Only fetch recent finished if we have API quota remaining
        if self.get_api_usage_stats()['remaining'] > 10:
            try:
                finished_data = self.fetch_recent_finished_fixtures()
                if finished_data:
                    created, updated = self.save_fixtures(finished_data)
                    stats['recent_finished_created'] = created
                    stats['recent_finished_updated'] = updated
                    stats['api_requests_used'] += 1
            except Exception as e:
                stats['errors'].append(f"Recent finished fixtures error: {e}")
        
        return stats

    def save_fixtures(self, api_response):
        """
        Parse and save fixtures from API response to database

        Args:
            api_response: JSON response from API-Football

        Returns:
            tuple: (created_count, updated_count)
        """
        if not api_response or 'response' not in api_response:
            return 0, 0

        created_count = 0
        updated_count = 0

        for fixture_data in api_response['response']:
            try:
                # Extract data from API response
                fixture_info = fixture_data['fixture']
                league_info = fixture_data['league']
                teams_info = fixture_data['teams']
                goals_info = fixture_data['goals']
                score_info = fixture_data['score']

                # Create or update League
                league, _ = League.objects.update_or_create(
                    api_id=league_info['id'],
                    season=league_info['season'],
                    defaults={
                        'name': league_info['name'],
                        'country': league_info['country'],
                        'logo': league_info.get('logo'),
                        'flag': league_info.get('flag'),
                        'round': league_info.get('round'),
                    }
                )

                # Create or update Home Team
                home_team, _ = Team.objects.update_or_create(
                    api_id=teams_info['home']['id'],
                    defaults={
                        'name': teams_info['home']['name'],
                        'logo': teams_info['home'].get('logo'),
                    }
                )

                # Create or update Away Team
                away_team, _ = Team.objects.update_or_create(
                    api_id=teams_info['away']['id'],
                    defaults={
                        'name': teams_info['away']['name'],
                        'logo': teams_info['away'].get('logo'),
                    }
                )

                # Create or update Venue
                venue = None
                if fixture_info.get('venue'):
                    venue_data = fixture_info['venue']
                    if venue_data.get('id'):
                        venue, _ = Venue.objects.update_or_create(
                            api_id=venue_data['id'],
                            defaults={
                                'name': venue_data.get('name'),
                                'city': venue_data.get('city'),
                            }
                        )

                # Create or update Fixture
                fixture, created = Fixture.objects.update_or_create(
                    api_id=fixture_info['id'],
                    defaults={
                        'referee': fixture_info.get('referee'),
                        'timezone': fixture_info['timezone'],
                        'date': datetime.fromisoformat(fixture_info['date'].replace('Z', '+00:00')),
                        'timestamp': fixture_info['timestamp'],
                        'venue': venue,
                        'status_long': fixture_info['status']['long'],
                        'status_short': fixture_info['status']['short'],
                        'elapsed': fixture_info['status'].get('elapsed'),
                        'league': league,
                        'home_team': home_team,
                        'away_team': away_team,
                        'home_goals': goals_info.get('home'),
                        'away_goals': goals_info.get('away'),
                        'home_goals_halftime': score_info.get('halftime', {}).get('home'),
                        'away_goals_halftime': score_info.get('halftime', {}).get('away'),
                        'home_goals_fulltime': score_info.get('fulltime', {}).get('home'),
                        'away_goals_fulltime': score_info.get('fulltime', {}).get('away'),
                        'home_goals_extratime': score_info.get('extratime', {}).get('home'),
                        'away_goals_extratime': score_info.get('extratime', {}).get('away'),
                        'home_goals_penalty': score_info.get('penalty', {}).get('home'),
                        'away_goals_penalty': score_info.get('penalty', {}).get('away'),
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1

            except Exception as e:
                print(f"Error saving fixture {fixture_info.get('id')}: {e}")
                continue

        return created_count, updated_count

    def get_api_usage_stats(self):
        """Get current API usage statistics"""
        today_count = APIUsageLog.get_daily_count()
        cached_count = APIUsageLog.objects.filter(
            date=dt_date.today(),
            response_cached=True
        ).count()

        return {
            'date': dt_date.today(),
            'total_requests': today_count + cached_count,
            'api_requests': today_count,
            'cached_requests': cached_count,
            'remaining': self.daily_limit - today_count,
            'limit': self.daily_limit,
            'percentage_used': (today_count / self.daily_limit) * 100 if self.daily_limit > 0 else 0
        }

    def fetch_specific_fixture(self, fixture_id):
        """
        Fetch a specific fixture by its API ID
        
        Args:
            fixture_id: API fixture ID to fetch
            
        Returns:
            dict: API response data for the specific fixture
        """
        if not self._can_make_request():
            print(f"WARNING: API limit reached, cannot fetch fixture {fixture_id}")
            return None
            
        params = {'id': fixture_id}
        url = f"{self.BASE_URL}/fixtures"
        
        try:
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            data = response.json()
            
            self._log_request('fixtures_specific', params, cached=False)
            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching fixture {fixture_id}: {e}")
            return None

    def detect_stuck_matches(self):
        """
        Detect matches that have been in live status for too long
        
        Returns:
            QuerySet: Fixtures that appear to be stuck
        """
        from django.utils import timezone
        from datetime import timedelta
        from django.db.models import Q
        
        now = timezone.now()
        
        # Find matches that are in live status AND either:
        # 1. Started more than 2 hours ago (normal match = 90min + 15min break + 30min buffer)
        # 2. OR elapsed time > 120 minutes
        stuck_threshold = now - timedelta(hours=2)
        
        stuck_matches = Fixture.objects.filter(
            status_short__in=['1H', '2H', 'HT', 'ET', 'P']
        ).filter(
            Q(date__lt=stuck_threshold) | Q(elapsed__gt=120)
        ).order_by('date')
        
        return stuck_matches

    def recover_stuck_match(self, fixture):
        """
        Attempt to recover a stuck match by fetching its current status
        
        Args:
            fixture: Fixture object that appears stuck
            
        Returns:
            bool: True if successfully updated, False otherwise
        """
        print(f"Attempting to recover stuck match: {fixture.home_team.name} vs {fixture.away_team.name} (ID: {fixture.api_id})")
        
        api_data = self.fetch_specific_fixture(fixture.api_id)
        if not api_data or not api_data.get('response'):
            print(f"  Failed to fetch data for fixture {fixture.api_id}")
            return False
            
        try:
            fixture_data = api_data['response'][0]
            updated_count = self.save_fixtures(api_data)[1]
            
            if updated_count > 0:
                # Refresh from DB to get updated data
                fixture.refresh_from_db()
                print(f"  ✅ Successfully updated: {fixture.status_long} ({fixture.status_short})")
                return True
            else:
                print(f"  ➡️ No update needed - data already current")
                return True
                
        except Exception as e:
            print(f"  ❌ Error processing update for fixture {fixture.api_id}: {e}")
            return False

    def run_stuck_match_recovery(self):
        """
        Run the stuck match detection and recovery process
        
        Returns:
            dict: Statistics about the recovery process
        """
        stuck_matches = self.detect_stuck_matches()
        
        stats = {
            'stuck_matches_found': stuck_matches.count(),
            'recovered_successfully': 0,
            'recovery_failed': 0,
            'api_requests_used': 0
        }
        
        if stats['stuck_matches_found'] == 0:
            return stats
            
        print(f"Found {stats['stuck_matches_found']} potentially stuck matches")
        
        # Limit recovery attempts to preserve API quota
        max_recoveries = min(20, self.daily_limit - APIUsageLog.get_daily_count())
        
        for fixture in stuck_matches[:max_recoveries]:
            if self.recover_stuck_match(fixture):
                stats['recovered_successfully'] += 1
            else:
                stats['recovery_failed'] += 1
            stats['api_requests_used'] += 1
            
        return stats


class LivescoreCzScraper:
    """
    Complementary free score scraper for https://www.livescore.cz/
    Updates the local Fixture database without consuming API-Football quotas.
    """
    BASE_URL = "https://www.livescore.cz/"

    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }

    def scrape_url(self, url: str) -> list:
        import re
        from bs4 import BeautifulSoup

        try:
            resp = requests.get(url, headers=self.headers, timeout=10)
            if resp.status_code != 200:
                return []
            
            soup = BeautifulSoup(resp.text, 'html.parser')
            score_div = soup.find('div', id='score-data')
            if not score_div:
                return []

            matches = []
            current_league = "Unknown League"

            for elem in score_div.find_all(['h4', 'a']):
                if elem.name == 'h4':
                    current_league = elem.get_text(strip=True)
                elif elem.name == 'a' and elem.get('href', '').startswith('/match/'):
                    match_class = elem.get('class', [])
                    score_text = elem.get_text(strip=True)

                    prev_text = ""
                    curr = elem.previous_sibling
                    while curr and curr.name not in ['br', 'h4']:
                        if isinstance(curr, str):
                            prev_text = curr + prev_text
                        elif curr.name == 'span':
                            prev_text = curr.get_text(strip=True) + " " + prev_text
                        curr = curr.previous_sibling

                    clean_text = prev_text.strip()
                    if '-' in clean_text:
                        clean_text = re.sub(r'^\d{1,2}:\d{2}', '', clean_text).strip()
                        clean_text = re.sub(r'^\d+\+?\'', '', clean_text).strip()

                        parts = clean_text.split('-')
                        if len(parts) >= 2:
                            home = parts[0].strip()
                            away = '-'.join(parts[1:]).strip()

                            home_name = re.sub(r'\s*\([A-Z][a-zA-Z]{1,3}\)$', '', home).strip()
                            away_name = re.sub(r'\s*\([A-Z][a-zA-Z]{1,3}\)$', '', away).strip()

                            status_short = 'NS'
                            if 'fin' in match_class:
                                status_short = 'FT'
                            elif 'live' in match_class:
                                status_short = '2H'

                            home_goals = None
                            away_goals = None
                            if '-' in score_text and status_short in ['FT', '2H', '1H']:
                                score_parts = score_text.split('-')
                                try:
                                    home_goals = int(score_parts[0].strip())
                                    away_goals = int(score_parts[1].strip())
                                except ValueError:
                                    pass

                            if home_name and away_name:
                                matches.append({
                                    'league': current_league,
                                    'home_team': home_name,
                                    'away_team': away_name,
                                    'home_goals': home_goals,
                                    'away_goals': away_goals,
                                    'status_short': status_short,
                                    'raw_score': score_text,
                                })

            return matches
        except Exception as e:
            print(f"Error scraping livescore.cz ({url}): {e}")
            return []

    def sync_scraped_scores(self, scraped_matches: list) -> dict:
        """
        Match scraped scores with database Fixtures and update them
        """
        from datetime import datetime, timedelta
        from django.utils import timezone
        from .models import Fixture, League, Team
        try:
            from fuzzywuzzy import fuzz
            calc_ratio = fuzz.ratio
        except ImportError:
            from difflib import SequenceMatcher
            def calc_ratio(s1, s2):
                return int(SequenceMatcher(None, str(s1), str(s2)).ratio() * 100)

        stats = {'scraped': len(scraped_matches), 'updated': 0, 'created': 0}
        now = timezone.now()

        for item in scraped_matches:
            if item['home_goals'] is None or item['away_goals'] is None:
                continue

            start_date = now - timedelta(days=2)
            end_date = now + timedelta(days=2)

            fixtures = Fixture.objects.filter(
                date__gte=start_date,
                date__lte=end_date
            ).select_related('home_team', 'away_team')

            matched_fixture = None
            best_score = 0
            threshold = 70

            for fix in fixtures:
                home_sim = calc_ratio(item['home_team'].lower(), fix.home_team.name.lower())
                away_sim = calc_ratio(item['away_team'].lower(), fix.away_team.name.lower())
                avg_sim = (home_sim + away_sim) / 2

                if home_sim >= threshold and away_sim >= threshold and avg_sim > best_score:
                    best_score = avg_sim
                    matched_fixture = fix

            if matched_fixture:
                matched_fixture.home_goals = item['home_goals']
                matched_fixture.away_goals = item['away_goals']
                matched_fixture.status_short = item['status_short']
                if item['status_short'] == 'FT':
                    matched_fixture.status_long = 'Match Finished'
                matched_fixture.save()
                stats['updated'] += 1
            else:
                try:
                    league, _ = League.objects.get_or_create(
                        name=item['league'][:100],
                        defaults={'api_id': abs(hash(item['league'])) % 1000000, 'season': now.year, 'country': 'World'}
                    )
                    home_team, _ = Team.objects.get_or_create(
                        name=item['home_team'][:100],
                        defaults={'api_id': abs(hash(item['home_team'])) % 1000000}
                    )
                    away_team, _ = Team.objects.get_or_create(
                        name=item['away_team'][:100],
                        defaults={'api_id': abs(hash(item['away_team'])) % 1000000}
                    )

                    fake_api_id = abs(hash(f"{item['home_team']}_{item['away_team']}_{now.strftime('%Y-%m-%d')}")) % 2000000000
                    Fixture.objects.update_or_create(
                        api_id=fake_api_id,
                        defaults={
                            'timezone': 'UTC',
                            'date': now,
                            'timestamp': int(now.timestamp()),
                            'status_long': 'Match Finished' if item['status_short'] == 'FT' else 'In Progress',
                            'status_short': item['status_short'],
                            'league': league,
                            'home_team': home_team,
                            'away_team': away_team,
                            'home_goals': item['home_goals'],
                            'away_goals': item['away_goals'],
                        }
                    )
                    stats['created'] += 1
                except Exception as create_err:
                    print(f"Error creating fixture for {item['home_team']} vs {item['away_team']}: {create_err}")

        return stats

    def scrape_and_sync(self) -> dict:
        """Fetch today and yesterday scores from livescore.cz and sync to DB"""
        today_matches = self.scrape_url(self.BASE_URL)
        yesterday_matches = self.scrape_url(f"{self.BASE_URL}?d=-1")

        combined = today_matches + yesterday_matches
        return self.sync_scraped_scores(combined)

