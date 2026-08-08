import logging
import urllib.request
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class LivescoreCzScraper:
    """
    Lightweight, reliable HTML scraper for https://www.livescore.cz/
    Does not require headless browser automation (Playwright/Selenium).
    """

    BASE_URL = "https://www.livescore.cz/"
    USER_AGENT = (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, Gecko) Chrome/120.0.0.0 Safari/537.36"
    )

    def __init__(self, timeout: int = 15):
        self.timeout = timeout

    def fetch_scores(self, day_offset: int = 0, status_filter: str = "all") -> List[Dict[str, Any]]:
        """
        Fetch and parse match results from livescore.cz.

        :param day_offset: 0 for Today, -1 for Yesterday, 1 for Tomorrow, etc.
        :param status_filter: 'all' (s=1), 'live' (s=2), 'finished' (s=3)
        :return: List of dicts with keys: league, time, home_team, away_team, score, home_goals, away_goals, status
        """
        status_map = {"all": 1, "live": 2, "finished": 3}
        s_val = status_map.get(status_filter, 1)

        url = f"{self.BASE_URL}?d={day_offset}&s={s_val}"
        logger.info(f"Fetching scores from {url}")

        req = urllib.request.Request(url, headers={"User-Agent": self.USER_AGENT})
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                html = resp.read().decode("utf-8")
        except Exception as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return []

        return self.parse_html(html)

    def parse_html(self, html: str) -> List[Dict[str, Any]]:
        """Parse raw HTML string from livescore.cz."""
        soup = BeautifulSoup(html, "html.parser")
        score_div = soup.find("div", id="score-data")
        if not score_div:
            logger.warning("Could not find <div id='score-data'> in HTML content")
            return []

        matches = []
        current_league = "Unknown League"

        for elem in score_div.children:
            if elem.name == "h4":
                # Clean league header, removing 'Standings' link text if attached
                header_text = elem.get_text().split("Standings")[0].strip()
                if header_text:
                    current_league = header_text
            elif elem.name == "span":
                time_str = elem.get_text().strip()
                next_sibling = elem.next_sibling
                if next_sibling and isinstance(next_sibling, str):
                    teams_raw = next_sibling.strip()
                    if " - " in teams_raw:
                        home_team, away_team = [t.strip() for t in teams_raw.split(" - ", 1)]
                        
                        a_tag = elem.find_next_sibling("a")
                        score_str = a_tag.get_text().strip() if a_tag else "-"
                        match_path = a_tag.get("href", "") if a_tag else ""
                        status_class = a_tag.get("class", [""])[0] if a_tag else "sched"

                        # Status mapping
                        # 'fin' -> Finished, 'live' -> In Progress, 'sched' -> Scheduled
                        status = "finished" if status_class == "fin" else ("live" if status_class == "live" else "scheduled")

                        home_goals = None
                        away_goals = None
                        if "-" in score_str and score_str != "-":
                            parts = score_str.split("-")
                            if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                                home_goals = int(parts[0])
                                away_goals = int(parts[1])

                        matches.append({
                            "league": current_league,
                            "time": time_str,
                            "home_team": home_team,
                            "away_team": away_team,
                            "score": score_str,
                            "home_goals": home_goals,
                            "away_goals": away_goals,
                            "status": status,
                            "status_raw": status_class,
                            "match_path": match_path,
                        })

        logger.info(f"Successfully scraped {len(matches)} matches from livescore.cz")
        return matches
