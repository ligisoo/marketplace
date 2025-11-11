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
    DAILY_LIMIT = 500  # API request limit per day

    def __init__(self):
        self.api_key = settings.API_FOOTBALL_KEY
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
        return APIUsageLog.can_make_request(self.DAILY_LIMIT)

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

            # Cache the response
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

            # Cache with shorter timeout for live matches
            cache.set(cache_key, data, self.CACHE_TIMEOUT_LIVE)
            self._log_request('fixtures', params, cached=False)

            return data
        except requests.exceptions.RequestException as e:
            print(f"Error fetching live fixtures: {e}")
            return None

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
            'remaining': self.DAILY_LIMIT - today_count,
            'limit': self.DAILY_LIMIT,
            'percentage_used': (today_count / self.DAILY_LIMIT) * 100
        }
