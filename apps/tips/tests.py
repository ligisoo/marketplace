from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from unittest.mock import patch, MagicMock
import os
import io
import json
from decimal import Decimal
from datetime import timedelta

from apps.tips.models import OCRProviderSettings, Tip, TipMatch
from apps.tips.betslip_extractor import process_betslip_image
from apps.tips.services.result_verifier import ResultVerifier
from apps.fixtures.models import Fixture, League, Team

# Dummy PNG image (1x1 transparent PNG)
DUMMY_PNG_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\xda\xed\xc1\x01\x01\x00\x00\x00\xc2\xa0\xf7Om\x00\x00\x00\x00IEND\xaeB`\x82'


class BetslipFastExtractorTests(TestCase):
    def setUp(self):
        super().setUp()
        self.original_gemini_api_key = os.getenv('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = 'fake-gemini-api-key'
        OCRProviderSettings.objects.all().delete()
        self.ocr_settings = OCRProviderSettings.objects.create(provider='gemini_langextract')

    def tearDown(self):
        super().tearDown()
        if self.original_gemini_api_key:
            os.environ['GEMINI_API_KEY'] = self.original_gemini_api_key
        else:
            del os.environ['GEMINI_API_KEY']
        OCRProviderSettings.objects.all().delete()

    @patch('apps.tips.betslip_extractor.extract_betslip_turbo')
    def test_process_betslip_image_success(self, mock_extract):
        # Mock the fast extractor return value directly
        mock_extract.return_value = {
            "success": True,
            "data": {
                "is_placed_slip": True,
                "matches": [
                    {
                        "match_date": "23/07/26",
                        "match_time": "18:00",
                        "home_team": "Team A",
                        "away_team": "Team B",
                        "bet_type": "1X2",
                        "pick": "Home",
                        "odds": 1.50
                    }
                ],
                "summary": {
                    "total_odds": 1.50,
                    "calc_odds": 1.50
                }
            }
        }

        result = process_betslip_image(DUMMY_PNG_BYTES)
        self.assertTrue(result['success'])
        self.assertEqual(result['data']['total_odds'], 1.5)
        self.assertEqual(len(result['data']['matches']), 1)
        self.assertEqual(result['data']['matches'][0]['home_team'], 'Team A')

    def test_ocr_provider_settings_get_active_provider(self):
        # Test default
        OCRProviderSettings.objects.all().delete()
        self.assertEqual(OCRProviderSettings.get_active_provider(), 'gemini_langextract')

        # Test setting update
        OCRProviderSettings.objects.create(provider='easyocr')
        self.assertEqual(OCRProviderSettings.get_active_provider(), 'easyocr')


class ResultVerifierTests(TestCase):
    def setUp(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.tipster = User.objects.create_user(username='test_tipster', password='password123')
        
        # Setup common models
        self.league = League.objects.create(api_id=1, name="Premier League", country="England", season=2026)
        self.team_home = Team.objects.create(api_id=10, name="Arsenal")
        self.team_away = Team.objects.create(api_id=11, name="Chelsea")

    def test_check_market_result_over_under(self):
        verifier = ResultVerifier()
        
        # Over 2.5 goals
        self.assertTrue(verifier._check_market_result("Over 2.5", "Over", 2, 1))
        self.assertFalse(verifier._check_market_result("Over 2.5", "Over", 1, 1))
        
        # Over/Under with +2.5 selection format
        self.assertTrue(verifier._check_market_result("Total Goals Over 2.5", "+2.5", 3, 0))
        self.assertFalse(verifier._check_market_result("Total Goals Over 2.5", "+2.5", 1, 1))
        
        # Under 2.5 goals
        self.assertTrue(verifier._check_market_result("Under 2.5", "Under", 1, 1))
        self.assertFalse(verifier._check_market_result("Under 2.5", "Under", 2, 1))

    def test_check_market_result_1x2(self):
        verifier = ResultVerifier()
        
        # Home Win
        self.assertTrue(verifier._check_market_result("1X2", "1", 2, 1))
        self.assertFalse(verifier._check_market_result("1X2", "1", 1, 1))
        self.assertFalse(verifier._check_market_result("1X2", "1", 1, 2))
        
        # Draw
        self.assertTrue(verifier._check_market_result("Match Result", "X", 1, 1))
        self.assertFalse(verifier._check_market_result("Match Result", "X", 2, 1))

    def test_check_market_result_btts(self):
        verifier = ResultVerifier()
        
        # Yes
        self.assertTrue(verifier._check_market_result("Both Teams to Score", "Yes", 2, 1))
        self.assertFalse(verifier._check_market_result("Both Teams to Score", "Yes", 2, 0))
        
        # No
        self.assertTrue(verifier._check_market_result("Both Teams to Score", "No", 2, 0))
        self.assertFalse(verifier._check_market_result("Both Teams to Score", "No", 2, 1))

    def test_check_market_result_double_chance(self):
        verifier = ResultVerifier()
        
        # 1X
        self.assertTrue(verifier._check_market_result("Double Chance", "1X", 1, 0))
        self.assertTrue(verifier._check_market_result("Double Chance", "1X", 1, 1))
        self.assertFalse(verifier._check_market_result("Double Chance", "1X", 0, 1))

    def test_check_market_result_draw_no_bet(self):
        verifier = ResultVerifier()
        
        # DNB Home Win
        self.assertTrue(verifier._check_market_result("Draw No Bet", "1", 2, 1))
        self.assertFalse(verifier._check_market_result("Draw No Bet", "1", 1, 2))
        
        # DNB Draw -> should return 'void'
        self.assertEqual(verifier._check_market_result("Draw No Bet", "1", 1, 1), 'void')

    def test_check_market_result_handicap(self):
        verifier = ResultVerifier()
        
        # Home +0.50
        self.assertTrue(verifier._check_market_result("Asian Handicap", "Arsenal [+0.50]", 1, 1, "Arsenal", "Chelsea"))
        self.assertFalse(verifier._check_market_result("Asian Handicap", "Arsenal [+0.50]", 0, 1, "Arsenal", "Chelsea"))
        
        # Home -0.50
        self.assertTrue(verifier._check_market_result("Asian Handicap", "Arsenal [-0.50]", 2, 1, "Arsenal", "Chelsea"))
        self.assertFalse(verifier._check_market_result("Asian Handicap", "Arsenal [-0.50]", 1, 1, "Arsenal", "Chelsea"))

    def test_verify_tips_with_concluded_and_void_matches(self):
        # Create a Tip
        tip = Tip.objects.create(
            tipster=self.tipster,
            bet_code="TESTVOID",
            odds=Decimal("3.00"),
            status="active",
            expires_at=timezone.now() + timedelta(hours=2)
        )
        
        # Create two TipMatch records
        match1 = TipMatch.objects.create(
            tip=tip,
            home_team="Arsenal",
            away_team="Chelsea",
            market="1X2",
            selection="1",
            odds=Decimal("1.50"),
            match_date=timezone.now() - timedelta(hours=4),
            api_match_id="100"
        )
        
        match2 = TipMatch.objects.create(
            tip=tip,
            home_team="Man Utd",
            away_team="Liverpool",
            market="1X2",
            selection="2",
            odds=Decimal("2.00"),
            match_date=timezone.now() - timedelta(hours=4),
            api_match_id="200"
        )
        
        # Create Fixtures in DB: match1 is a win (Arsenal 2-1 Chelsea), match2 is postponed (PST)
        Fixture.objects.create(
            api_id=100,
            timezone="UTC",
            date=match1.match_date,
            timestamp=int(match1.match_date.timestamp()),
            status_long="Match Finished",
            status_short="FT",
            league=self.league,
            home_team=self.team_home,
            away_team=self.team_away,
            home_goals=2,
            away_goals=1
        )
        
        Fixture.objects.create(
            api_id=200,
            timezone="UTC",
            date=match2.match_date,
            timestamp=int(match2.match_date.timestamp()),
            status_long="Match Postponed",
            status_short="PST",
            league=self.league,
            home_team=self.team_home,
            away_team=self.team_away,
            home_goals=None,
            away_goals=None
        )
        
        verifier = ResultVerifier()
        stats = verifier.verify_tips()
        
        # Verify stats
        self.assertEqual(stats['tips_verified'], 1)
        self.assertEqual(stats['tips_won'], 1)
        
        # Refresh from DB
        tip.refresh_from_db()
        match1.refresh_from_db()
        match2.refresh_from_db()
        
        # Verify Tip properties
        self.assertTrue(tip.is_resulted)
        self.assertTrue(tip.is_won)
        self.assertEqual(tip.status, 'archived')
        # Total odds should recalculate to match1.odds * match2.odds = 1.50 * 1.00 = 1.50
        self.assertEqual(tip.odds, Decimal("1.50"))
        
        # Verify match statuses
        self.assertTrue(match1.is_resulted)
        self.assertTrue(match1.is_won)
        self.assertEqual(match1.actual_result, "FT 2-1")
        
        self.assertTrue(match2.is_resulted)
        self.assertTrue(match2.is_won)  # void treated as won so accumulator continues
        self.assertEqual(match2.odds, Decimal("1.00"))
        self.assertIn("Void / Push", match2.actual_result)