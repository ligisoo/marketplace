from datetime import datetime
import json
import os
import time
import requests

API_KEY = os.getenv("FOOTBALL_API_KEY", "69db687a2df6b40ad9691d5d08063801")
API_URL = "https://v3.football.api-sports.io/fixtures"
CACHE_FILE = ".fixtures_cache.json"


def get_todays_fixtures(api_key: str = API_KEY, cache_ttl_seconds: int = 300):
    """Fetch today's fixtures (live, finished, and upcoming) from API-Football."""
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. Read from local cache if fresh (< cache_ttl_seconds)
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, "r") as f:
                cached = json.load(f)
                age = time.time() - cached.get("timestamp", 0)
                if cached.get("date") == today_str and age < cache_ttl_seconds:
                    print(f"📦 [CACHE] Using local response ({int(age)}s old)")
                    return cached.get("payload", [])
        except (json.JSONDecodeError, OSError):
            pass

    # 2. Make fresh API request for today's date
    headers = {"x-apisports-key": api_key}
    params = {"date": today_str}

    try:
        response = requests.get(API_URL, headers=headers, params=params, timeout=10)
        remaining = response.headers.get("x-ratelimit-requests-remaining", "N/A")
        print(f"📡 API Request OK | Daily Quota Remaining: {remaining}/100")

        response.raise_for_status()
        payload = response.json().get("response", [])

        # Save to local cache
        try:
            with open(CACHE_FILE, "w") as f:
                json.dump({"date": today_str, "timestamp": time.time(), "payload": payload}, f)
        except OSError:
            pass

        return payload

    except requests.exceptions.RequestException as err:
        print(f"❌ Request Error: {err}")
        return []


def display_fixtures(fixtures):
    """Display categorized summary of today's matches."""
    if not fixtures:
        print("No matches found for today.")
        return

    live, finished, upcoming = [], [], []

    for item in fixtures:
        status = item["fixture"]["status"]["short"]
        home = item["teams"]["home"]["name"]
        away = item["teams"]["away"]["name"]
        gh = item["goals"]["home"]
        ga = item["goals"]["away"]

        score = f"{gh} - {ga}" if gh is not None else "vs"
        match_str = f"{home} {score} {away} ({status})"

        if status in ["1H", "HT", "2H", "ET", "P", "LIVE"]:
            live.append(match_str)
        elif status in ["FT", "AET", "PEN"]:
            finished.append(match_str)
        else:
            upcoming.append(match_str)

    print(f"\n🔴 LIVE MATCHES ({len(live)}):")
    for m in live:
        print(f"  • {m}")

    print(f"\n🏁 FINISHED MATCHES ({len(finished)}):")
    for m in finished[:10]:
        print(f"  • {m}")
    if len(finished) > 10:
        print(f"  ... and {len(finished) - 10} more finished matches")

    print(f"\n📅 UPCOMING MATCHES ({len(upcoming)}):")
    for m in upcoming[:5]:
        print(f"  • {m}")


class APIFootballService:
    """Lightweight API-Football Service wrapper for Django models integration."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or API_KEY

    def _can_make_request(self):
        return True

    def get_api_usage_stats(self):
        return {
            'total_requests': 0,
            'api_requests': 0,
            'cached_requests': 0,
            'remaining': 100,
            'limit': 100,
            'percentage_used': 0.0
        }

    def fetch_fixtures(self, date=None, use_cache=True, force_refresh=False):
        today_str = datetime.now().strftime("%Y-%m-%d")
        date_str = date.strftime("%Y-%m-%d") if hasattr(date, "strftime") else (str(date) if date else today_str)

        if date_str == today_str:
            payload = get_todays_fixtures(api_key=self.api_key, cache_ttl_seconds=0 if force_refresh else 300)
            return {"response": payload}

        headers = {"x-apisports-key": self.api_key}
        params = {"date": date_str}
        try:
            res = requests.get(API_URL, headers=headers, params=params, timeout=10)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as err:
            print(f"❌ Request Error: {err}")
            return {"response": []}

    def fetch_live_fixtures(self, use_cache=True):
        headers = {"x-apisports-key": self.api_key}
        params = {"live": "all"}
        try:
            res = requests.get(API_URL, headers=headers, params=params, timeout=10)
            res.raise_for_status()
            return res.json()
        except requests.exceptions.RequestException as err:
            print(f"❌ Request Error: {err}")
            return {"response": []}

    def save_fixtures(self, api_response):
        """Save fixtures list or API response dict into Django database models."""
        from .models import League, Team, Venue, Fixture

        if not api_response:
            return 0, 0

        if isinstance(api_response, dict):
            items = api_response.get("response", [])
        elif isinstance(api_response, list):
            items = api_response
        else:
            items = []

        created_count = 0
        updated_count = 0

        for fixture_data in items:
            try:
                fixture_info = fixture_data["fixture"]
                league_info = fixture_data["league"]
                teams_info = fixture_data["teams"]
                goals_info = fixture_data.get("goals", {})
                score_info = fixture_data.get("score", {})

                league, _ = League.objects.update_or_create(
                    api_id=league_info["id"],
                    season=league_info["season"],
                    defaults={
                        "name": league_info["name"],
                        "country": league_info.get("country", ""),
                        "logo": league_info.get("logo"),
                        "flag": league_info.get("flag"),
                        "round": league_info.get("round"),
                    }
                )

                home_team, _ = Team.objects.update_or_create(
                    api_id=teams_info["home"]["id"],
                    defaults={
                        "name": teams_info["home"]["name"],
                        "logo": teams_info["home"].get("logo"),
                    }
                )

                away_team, _ = Team.objects.update_or_create(
                    api_id=teams_info["away"]["id"],
                    defaults={
                        "name": teams_info["away"]["name"],
                        "logo": teams_info["away"].get("logo"),
                    }
                )

                venue = None
                if fixture_info.get("venue") and fixture_info["venue"].get("id"):
                    v_data = fixture_info["venue"]
                    venue, _ = Venue.objects.update_or_create(
                        api_id=v_data["id"],
                        defaults={
                            "name": v_data.get("name"),
                            "city": v_data.get("city"),
                        }
                    )

                fixture, created = Fixture.objects.update_or_create(
                    api_id=fixture_info["id"],
                    defaults={
                        "referee": fixture_info.get("referee"),
                        "timezone": fixture_info.get("timezone", "UTC"),
                        "date": datetime.fromisoformat(fixture_info["date"].replace("Z", "+00:00")),
                        "timestamp": fixture_info.get("timestamp", 0),
                        "venue": venue,
                        "status_long": fixture_info["status"].get("long", ""),
                        "status_short": fixture_info["status"].get("short", ""),
                        "elapsed": fixture_info["status"].get("elapsed"),
                        "league": league,
                        "home_team": home_team,
                        "away_team": away_team,
                        "home_goals": goals_info.get("home"),
                        "away_goals": goals_info.get("away"),
                        "home_goals_halftime": score_info.get("halftime", {}).get("home"),
                        "away_goals_halftime": score_info.get("halftime", {}).get("away"),
                        "home_goals_fulltime": score_info.get("fulltime", {}).get("home"),
                        "away_goals_fulltime": score_info.get("fulltime", {}).get("away"),
                        "home_goals_extratime": score_info.get("extratime", {}).get("home"),
                        "away_goals_extratime": score_info.get("extratime", {}).get("away"),
                        "home_goals_penalty": score_info.get("penalty", {}).get("home"),
                        "away_goals_penalty": score_info.get("penalty", {}).get("away"),
                    }
                )

                if created:
                    created_count += 1
                else:
                    updated_count += 1
            except Exception as e:
                print(f"Error saving fixture {fixture_data.get('fixture', {}).get('id')}: {e}")
                continue

        return created_count, updated_count


if __name__ == "__main__":
    matches = get_todays_fixtures(cache_ttl_seconds=300)
    display_fixtures(matches)
