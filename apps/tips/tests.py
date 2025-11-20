from django.test import TestCase
from django.conf import settings
from django.utils import timezone
from unittest.mock import patch, MagicMock
import os
import io
import json
from datetime import timedelta

from .ocr import BetslipOCR
from .models import OCRProviderSettings

# Dummy PNG image (1x1 transparent PNG)
# This is a minimal valid PNG. Real images would be larger.
DUMMY_PNG_BYTES = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\x0cIDATx\xda\xed\xc1\x01\x01\x00\x00\x00\xc2\xa0\xf7Om\x00\x00\x00\x00IEND\xaeB`\x82'

class BetslipOCRTests(TestCase):

    def setUp(self):
        super().setUp()
        self.original_gemini_api_key = os.getenv('GEMINI_API_KEY')
        os.environ['GEMINI_API_KEY'] = 'fake-gemini-api-key'

        # Ensure a default OCRProviderSettings exists or is updated
        # Clear all first to ensure a clean state before creating/updating
        OCRProviderSettings.objects.all().delete()
        self.ocr_settings, created = OCRProviderSettings.objects.get_or_create(
            provider='textract',
            defaults={'updated_by': None} # Assuming updated_by can be null for tests
        )

    def tearDown(self):
        super().tearDown()
        if self.original_gemini_api_key:
            os.environ['GEMINI_API_KEY'] = self.original_gemini_api_key
        else:
            del os.environ['GEMINI_API_KEY']
        
        # Clean up any OCRProviderSettings created
        OCRProviderSettings.objects.all().delete()

    @patch('google.genai.Client')
    @patch('google.genai.types.Part.from_bytes')
    def test_extract_with_gemini_success(self, mock_from_bytes, mock_gemini_client):
        # Update the existing OCRProviderSettings for this test
        self.ocr_settings.provider = 'gemini'
        self.ocr_settings.save()

        ocr_service = BetslipOCR(provider='gemini')

        # Mock the Gemini API response
        mock_response = MagicMock()
        mock_response.text = json.dumps({
            "bet_code": "JYRCAV",
            "matches": [
                {
                    "teams": "Team A - Team B",
                    "home_team": "Team A",
                    "away_team": "Team B",
                    "bet_type": "3 Way",
                    "pick": "Home",
                    "odds": "1.50"
                }
            ],
            "summary": {
                "total_odds": "1.50",
                "bet_amount": "100.00",
                "currency": "KSH",
                "possible_win": "150.00"
            }
        })
        mock_gemini_client.return_value.models.generate_content.return_value = mock_response
        mock_from_bytes.return_value = "mock_image_part"

        image_bytes = DUMMY_PNG_BYTES
        result = ocr_service._extract_with_gemini(image_bytes)

        self.assertTrue(result['success'])
        self.assertIn('gemini_structured_data', result)
        self.assertEqual(result['gemini_structured_data']['bet_code'], 'JYRCAV')
        self.assertEqual(len(result['gemini_structured_data']['matches']), 1)
        self.assertEqual(result['gemini_structured_data']['summary']['total_odds'], '1.50')
        self.assertEqual(result['text_blocks'], [])
        mock_gemini_client.return_value.models.generate_content.assert_called_once()
        mock_from_bytes.assert_called_once_with(data=image_bytes, mime_type='image/png')

    @patch('google.genai.Client')
    @patch('google.genai.types.Part.from_bytes')
    def test_extract_with_gemini_no_api_key(self, mock_from_bytes, mock_gemini_client):
        # Update the existing OCRProviderSettings for this test
        self.ocr_settings.provider = 'gemini'
        self.ocr_settings.save()

        ocr_service = BetslipOCR(provider='gemini')
        del os.environ['GEMINI_API_KEY'] # Temporarily remove API key

        image_bytes = DUMMY_PNG_BYTES
        result = ocr_service._extract_with_gemini(image_bytes)

        self.assertFalse(result['success'])
        self.assertIn('Gemini API key not configured', result['error'])
        mock_gemini_client.return_value.models.generate_content.assert_not_called()
        mock_from_bytes.assert_not_called()
        os.environ['GEMINI_API_KEY'] = 'fake-gemini-api-key' # Restore for other tests

    @patch('google.genai.Client')
    @patch('google.genai.types.Part.from_bytes')
    def test_extract_with_gemini_json_decode_error(self, mock_from_bytes, mock_gemini_client):
        # Update the existing OCRProviderSettings for this test
        self.ocr_settings.provider = 'gemini'
        self.ocr_settings.save()

        ocr_service = BetslipOCR(provider='gemini')

        mock_response = MagicMock()
        mock_response.text = "This is not valid JSON content" # Invalid JSON
        mock_gemini_client.return_value.models.generate_content.return_value = mock_response
        mock_from_bytes.return_value = "mock_image_part"

        image_bytes = DUMMY_PNG_BYTES
        result = ocr_service._extract_with_gemini(image_bytes)

        self.assertFalse(result['success'])
        self.assertIn('Failed to extract text from image using Gemini', result['error'])
        mock_gemini_client.return_value.models.generate_content.assert_called_once()
        mock_from_bytes.assert_called_once_with(data=image_bytes, mime_type='image/png')
    
    @patch('google.genai.Client')
    @patch('google.genai.types.Part.from_bytes')
    def test_process_betslip_image_with_gemini(self, mock_from_bytes, mock_gemini_client):
        # Update the existing OCRProviderSettings for this test
        self.ocr_settings.provider = 'gemini'
        self.ocr_settings.save()
        
        ocr_service = BetslipOCR() # Should pick up 'gemini' from settings

        mock_gemini_response_data = {
            "bet_code": "GEMINIBET",
            "matches": [
                {
                    "teams": "Home Team A - Away Team B",
                    "home_team": "Home Team A",
                    "away_team": "Away Team B",
                    "bet_type": "1X2",
                    "pick": "Draw",
                    "odds": "2.75"
                },
                {
                    "teams": "Team C - Team D",
                    "home_team": "Team C",
                    "away_team": "Team D",
                    "bet_type": "Over/Under 2.5",
                    "pick": "Over",
                    "odds": "1.90"
                }
            ],
            "summary": {
                "total_odds": "5.225", # 2.75 * 1.90 = 5.225
                "bet_amount": "200.00",
                "currency": "KSH",
                "possible_win": "1045.00"
            }
        }

        mock_response = MagicMock()
        mock_response.text = json.dumps(mock_gemini_response_data)
        mock_gemini_client.return_value.models.generate_content.return_value = mock_response
        mock_from_bytes.return_value = "mock_image_part"

        image_file = io.BytesIO(DUMMY_PNG_BYTES)
        result = ocr_service.process_betslip_image(image_file)

        self.assertTrue(result['success'])
        self.assertIn('data', result)
        self.assertEqual(result['confidence'], 99.0)

        parsed_data = result['data']
        self.assertEqual(parsed_data['bet_code'], 'GEMINIBET')
        self.assertEqual(parsed_data['total_odds'], 5.225)
        self.assertEqual(parsed_data['possible_win'], 1045.00)
        self.assertEqual(len(parsed_data['matches']), 2)

        # Check first match
        match1 = parsed_data['matches'][0]
        self.assertEqual(match1['home_team'], 'Home Team A')
        self.assertEqual(match1['away_team'], 'Away Team B')
        self.assertEqual(match1['market'], '1X2')
        self.assertEqual(match1['selection'], 'Draw')
        self.assertEqual(match1['odds'], 2.75)
        self.assertIsInstance(timezone.datetime.fromisoformat(match1['match_date']), timezone.datetime)

        # Check second match
        match2 = parsed_data['matches'][1]
        self.assertEqual(match2['home_team'], 'Team C')
        self.assertEqual(match2['away_team'], 'Team D')
        self.assertEqual(match2['market'], 'Over/Under 2.5')
        self.assertEqual(match2['selection'], 'Over')
        self.assertEqual(match2['odds'], 1.90)

        # Check odds validation
        self.assertIn('odds_validation', parsed_data)
        self.assertTrue(parsed_data['odds_validation']['is_valid'])
        self.assertAlmostEqual(parsed_data['odds_validation']['calculated_odds'], 5.22, places=2)
        self.assertAlmostEqual(parsed_data['odds_validation']['extracted_odds'], 5.225, places=3)
        self.assertAlmostEqual(parsed_data['odds_validation']['difference'], 0.0, places=3)

        mock_gemini_client.return_value.models.generate_content.assert_called_once()
        mock_from_bytes.assert_called_once_with(data=DUMMY_PNG_BYTES, mime_type='image/png')

    @patch('google.genai.Client')
    @patch('google.genai.types.Part.from_bytes')
    def test_process_betslip_image_fallback_to_traditional_ocr(self, mock_from_bytes, mock_gemini_client):
        # Update the existing OCRProviderSettings for this test
        self.ocr_settings.provider = 'textract'
        self.ocr_settings.save()

        ocr_service = BetslipOCR() # Should pick up 'textract' from settings

        # Mock Textract/EasyOCR behavior - no gemini_structured_data
        # For simplicity, we'll mock the internal call to _extract_text_textract or _extract_text_easyocr
        # by patching the base extract_text_from_image, returning traditional text_blocks
        with patch.object(ocr_service, 'extract_text_from_image', return_value={
            'success': True,
            'text_blocks': [
                {'text': 'Bet Code: FALLBACK123', 'confidence': 95},
                {'text': 'Team X - Team Y', 'confidence': 90},
                {'text': 'Pick: Home', 'confidence': 92},
                {'text': 'Odds: 2.00', 'confidence': 93},
                {'text': 'Total Odds: 2.00', 'confidence': 96},
                {'text': 'Possible Win: 200.00', 'confidence': 94},
            ],
            'raw_response': {}
        }) as mock_extract_text:
            image_file = io.BytesIO(DUMMY_PNG_BYTES)
            result = ocr_service.process_betslip_image(image_file)

            self.assertTrue(result['success'])
            self.assertIn('data', result)
            self.assertNotEqual(result['confidence'], 99.0) # Should not be Gemini confidence

            parsed_data = result['data']
            self.assertEqual(parsed_data['bet_code'], 'FALLBACK123')
            self.assertEqual(parsed_data['total_odds'], 2.00)
            self.assertEqual(len(parsed_data['matches']), 1)
            # Ensure Gemini was NOT called
            mock_gemini_client.return_value.models.generate_content.assert_not_called()
            mock_from_bytes.assert_not_called()
            mock_extract_text.assert_called_once()

    def test_ocr_provider_settings_get_active_provider(self):
        # Test default when no settings exist
        OCRProviderSettings.objects.all().delete()
        self.assertEqual(OCRProviderSettings.get_active_provider(), 'textract')

        # Test with easyocr (update existing)
        self.ocr_settings.provider = 'easyocr'
        self.ocr_settings.save()
        self.assertEqual(OCRProviderSettings.get_active_provider(), 'easyocr')
        
        # Test with gemini (update existing)
        self.ocr_settings.provider = 'gemini'
        self.ocr_settings.save()
        self.assertEqual(OCRProviderSettings.get_active_provider(), 'gemini')