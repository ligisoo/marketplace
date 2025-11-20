import boto3
import json
import re
import logging
import asyncio
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from fuzzywuzzy import fuzz, process
import os

# Set up logging
logger = logging.getLogger(__name__)

# Lazy load EasyOCR to avoid import errors if not installed
_easyocr_reader = None


def get_easyocr_reader():
    """Lazy load EasyOCR reader"""
    global _easyocr_reader
    if _easyocr_reader is None:
        try:
            import easyocr
            logger.info("Loading EasyOCR model...")
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
            logger.info("EasyOCR model loaded successfully!")
        except ImportError:
            logger.error("EasyOCR is not installed. Please install it with: pip install easyocr opencv-python")
            raise
    return _easyocr_reader


class BetslipOCR:
    """OCR service for extracting betting information from betslip screenshots"""

    def __init__(self, provider=None):
        """
        Initialize OCR service with specified provider

        Args:
            provider: 'textract' or 'easyocr'. If None, will check settings.
        """
        if provider is None:
            # Import here to avoid circular dependency
            from .models import OCRProviderSettings
            provider = OCRProviderSettings.get_active_provider()

        self.provider = provider
        logger.info(f"Initializing BetslipOCR with provider: {self.provider}")

        # Initialize Textract client if needed
        if self.provider == 'textract':
            self.textract = boto3.client(
                'textract',
                aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
                aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
                region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
            )
        else:
            self.textract = None
        
        # Common betting markets for fuzzy matching (including Kenyan variations)
        self.common_markets = [
            # Goals markets
            'Over 2.5', 'Under 2.5', 'Over 1.5', 'Under 1.5', 'Over 3.5', 'Under 3.5',
            'Over 0.5', 'Under 0.5', 'Over 4.5', 'Under 4.5',
            'O2.5', 'U2.5', 'O1.5', 'U1.5', 'O3.5', 'U3.5',

            # BTTS markets
            'Both Teams to Score', 'BTTS', 'GG', 'NG', 'Both Teams Score',
            'GG/NG', 'Yes/No', 'Both Score',

            # Match Result markets
            '1X2', 'Match Result', 'Full Time Result', 'FT Result',
            'Home Win', 'Away Win', 'Draw', '1', 'X', '2',
            'Home', 'Away',

            # Double Chance
            'Double Chance', '1X', 'X2', '12',
            'Home or Draw', 'Away or Draw', 'Home or Away',

            # Other markets
            'Correct Score', 'Half Time Result', 'HT Result', 'HT/FT',
            'Total Goals', 'Asian Handicap', 'Handicap',
            'First Goal', 'Last Goal', 'Anytime Goalscorer',
            'Clean Sheet', 'Winning Margin',

            # Kenyan specific variations
            'Multibet', 'Multi Bet', 'MultiGoal'
        ]
        
        # Common team name patterns (Kenyan and international)
        self.team_patterns = [
            r'\b[A-Z][a-z]+\s+[A-Z][a-z]+\b',  # Two word team names
            r'\b[A-Z]{2,4}\b',  # Abbreviations
            r'\b[A-Z][a-z]+\b'  # Single word teams
        ]
    
    def extract_text_from_image(self, image_bytes):
        """Extract text from betslip image using configured OCR provider"""
        if self.provider == 'textract':
            return self._extract_text_textract(image_bytes)
        elif self.provider == 'easyocr':
            return self._extract_text_easyocr(image_bytes)
        elif self.provider == 'gemini':
            return self._extract_with_gemini(image_bytes)
        elif self.provider == 'gemini_langextract':
            return self._extract_with_gemini_langextract(image_bytes)
        else:
            logger.error(f"Unknown OCR provider: {self.provider}")
            return {
                'success': False,
                'error': f'Unknown OCR provider: {self.provider}',
                'text_blocks': []
            }

    def _extract_text_textract(self, image_bytes):
        """Extract text from betslip image using AWS Textract"""
        try:
            logger.info("Starting AWS Textract extraction")

            response = self.textract.detect_document_text(
                Document={'Bytes': image_bytes}
            )

            # Extract all text blocks
            text_blocks = []
            for block in response['Blocks']:
                if block['BlockType'] == 'LINE':
                    text_blocks.append({
                        'text': block['Text'],
                        'confidence': block['Confidence']
                    })

            logger.info(f"Successfully extracted {len(text_blocks)} text blocks from image")

            return {
                'success': True,
                'text_blocks': text_blocks,
                'raw_response': response
            }

        except self.textract.exceptions.InvalidParameterException as e:
            logger.error(f"Invalid parameter for Textract: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid image format or size. Please upload a clear image (max 5MB).',
                'text_blocks': []
            }
        except self.textract.exceptions.ProvisionedThroughputExceededException as e:
            logger.error(f"Textract throughput exceeded: {str(e)}")
            return {
                'success': False,
                'error': 'Service temporarily busy. Please try again in a moment.',
                'text_blocks': []
            }
        except Exception as e:
            logger.error(f"Textract extraction failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to extract text from image: {str(e)}',
                'text_blocks': []
            }

    def _extract_text_easyocr(self, image_bytes):
        """Extract text from betslip image using EasyOCR"""
        try:
            logger.info("Starting EasyOCR extraction")

            # Save bytes to temporary file for EasyOCR processing
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix='.png') as tmp_file:
                tmp_file.write(image_bytes)
                tmp_path = tmp_file.name

            try:
                # Preprocess image
                # Options: 'none', 'light', 'medium', 'heavy'
                # Using 'none' for best speed and 90%+ accuracy
                processed_path = self._preprocess_image(tmp_path, strategy='none')

                # Get EasyOCR reader
                reader = get_easyocr_reader()

                # Perform OCR
                results = reader.readtext(processed_path)

                # Convert to text blocks format
                text_blocks = []
                for (bbox, text, confidence) in results:
                    text_blocks.append({
                        'text': text,
                        'confidence': confidence * 100  # Convert to percentage like Textract
                    })

                logger.info(f"Successfully extracted {len(text_blocks)} text blocks from image using EasyOCR")

                return {
                    'success': True,
                    'text_blocks': text_blocks,
                    'raw_response': results
                }

            finally:
                # Clean up temporary files
                try:
                    os.remove(tmp_path)
                    if processed_path != tmp_path and os.path.exists(processed_path):
                        os.remove(processed_path)
                except Exception as cleanup_error:
                    logger.warning(f"Failed to clean up temporary files: {cleanup_error}")

        except ImportError:
            logger.error("EasyOCR is not installed")
            return {
                'success': False,
                'error': 'EasyOCR is not installed. Please contact the administrator.',
                'text_blocks': []
            }
        except Exception as e:
            logger.error(f"EasyOCR extraction failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to extract text from image: {str(e)}',
                'text_blocks': []
            }

    def _extract_with_gemini(self, image_bytes):
        """
        Fast betslip extraction using Gemini API.
        Combines OCR + structured extraction in one API call.
        Returns data in a format compatible with existing parsing logic.
        """
        try:
            logger.info("Starting Gemini extraction")

            import google.genai as genai
            from google.genai import types

            # Get API key from settings
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment")
                return {
                    'success': False,
                    'error': 'Gemini API key not configured',
                    'text_blocks': []
                }

            # Configure API client
            client = genai.Client(api_key=api_key)

            # Single prompt that does OCR + structured extraction
            prompt = """Analyze this betting slip image and extract all match information as JSON.

Output ONLY valid JSON in this exact format:
{
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
    "total_odds": "10.50",
    "bet_amount": "100.00",
    "currency": "KSH",
    "possible_win": "1,050.00"
  }
}

Rules:
1. Extract ONLY actual matches (teams vs teams with odds)
2. Do NOT extract footer text (TOTAL ODDS, BET AMOUNT are summary, not matches)
3. Use EXACT team names from the image
4. Each match must have: teams, home_team, away_team, bet_type, pick, odds
5. Extract the bet code/ID from the image
6. Extract total odds, bet amount, and possible win from the summary section
7. Output ONLY the JSON, no other text
"""

            # Make API call using gemini-2.5-flash (stable model with better quotas)
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    prompt,
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type='image/png'
                    )
                ],
                config=types.GenerateContentConfig(
                    temperature=0.1,
                    response_mime_type='application/json'
                )
            )

            # Parse JSON response
            try:
                result = json.loads(response.text)
                logger.info(f"Successfully extracted data using Gemini: {len(result.get('matches', []))} matches")

                # Return in a format that bypasses traditional parsing
                # We'll handle this specially in process_betslip_image
                return {
                    'success': True,
                    'gemini_structured_data': result,
                    'text_blocks': []  # Not used for Gemini
                }

            except json.JSONDecodeError as e:
                # Fallback: try to extract JSON from response
                import re
                json_match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if json_match:
                    result = json.loads(json_match.group())
                    logger.info(f"Successfully extracted data using Gemini (with regex): {len(result.get('matches', []))} matches")
                    return {
                        'success': True,
                        'gemini_structured_data': result,
                        'text_blocks': []
                    }
                else:
                    logger.error(f"Could not parse JSON from Gemini response: {response.text[:200]}")
                    raise ValueError(f"Could not parse JSON from response: {response.text[:200]}")

        except ImportError:
            logger.error("google-genai is not installed")
            return {
                'success': False,
                'error': 'Gemini API library is not installed. Please contact the administrator.',
                'text_blocks': []
            }
        except Exception as e:
            logger.error(f"Gemini extraction failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to extract text from image using Gemini: {str(e)}',
                'text_blocks': []
            }

    def _extract_with_gemini_langextract(self, image_bytes):
        """
        Extract betslip data using Gemini Vision OCR + LangExtract (EXACT langextract approach).

        This is the two-step process from /home/walter/langextract/betslip_gemini_ocr.py:
        1. Step 1: Use Gemini Vision API to extract raw OCR text
        2. Step 2: Pass OCR text to LangExtract for structured extraction

        Returns structured extraction result with matches and bet_summary.
        """
        try:
            logger.info("Starting Gemini Vision OCR + LangExtract extraction")
            import langextract as lx
            import textwrap
            import tempfile
            import google.genai as genai
            from google.genai import types

            # Get API key
            api_key = os.getenv('GEMINI_API_KEY')
            if not api_key:
                logger.error("GEMINI_API_KEY not found in environment")
                return {
                    'success': False,
                    'error': 'Gemini API key not configured',
                    'text_blocks': []
                }

            # ====== STEP 1: Gemini Vision API for OCR ======
            logger.info("Step 1: Extracting raw text using Gemini Vision API...")

            client = genai.Client(api_key=api_key)

            # OCR-focused prompt (from langextract)
            ocr_prompt = """Extract ALL text from this betting slip image.

IMPORTANT:
- Extract EVERY piece of text you can see
- Preserve the exact spelling and formatting
- Include team names, odds, amounts, and all labels
- Output only the raw text, line by line
- Do NOT interpret or structure the data
- Do NOT skip any text

Extract the text now:"""

            # Call Gemini Vision API for OCR
            response = client.models.generate_content(
                model='gemini-2.5-flash',
                contents=[
                    ocr_prompt,
                    types.Part.from_bytes(
                        data=image_bytes,
                        mime_type='image/png'
                    )
                ]
            )

            if not response.text:
                raise ValueError("No text extracted from image by Gemini Vision API")

            ocr_text = response.text.strip()
            logger.info(f"Gemini OCR extracted {len(ocr_text)} characters of text")
            logger.debug(f"OCR Text Preview: {ocr_text[:200]}...")

            # ====== STEP 2: LangExtract for Structured Extraction ======
            logger.info("Step 2: Extracting structured data using LangExtract...")

            # Define extraction prompt (from langextract)
            prompt = textwrap.dedent("""\
                Extract all match information and betting details from the betslip text.

                For each match, extract:
                - Team names EXACTLY as shown in the text
                - Bet type (e.g., 3 Way, Over/Under, etc.)
                - Pick/Selection (e.g., Home, Away, Draw)
                - Odds value (decimal format)

                Also extract overall bet details:
                - Total odds / Accumulator odds
                - Bet amount and currency
                - Possible win / Potential payout
                - Any taxes, bonuses, or boosts

                IMPORTANT: Use EXACT text from the input. Do not substitute or invent team names.
                Extract entities in the order they appear.""")

            # Define examples for few-shot learning (from langextract)
            examples = [
                lx.data.ExampleData(
                    text=textwrap.dedent("""\
                        Pisa - Lazio
                        3 Way
                        Your Pick: Home
                        3.69"""),
                    extractions=[
                        lx.data.Extraction(
                            extraction_class="match",
                            extraction_text="Pisa - Lazio",
                            attributes={
                                "home_team": "Pisa",
                                "away_team": "Lazio",
                                "bet_type": "3 Way",
                                "pick": "Home",
                                "odds": "3.69"
                            }
                        ),
                    ]
                ),
                lx.data.ExampleData(
                    text=textwrap.dedent("""\
                        RB Salzburg - WSG Wattens
                        3 Way
                        Your Pick: Home
                        1.34"""),
                    extractions=[
                        lx.data.Extraction(
                            extraction_class="match",
                            extraction_text="RB Salzburg - WSG Wattens",
                            attributes={
                                "home_team": "RB Salzburg",
                                "away_team": "WSG Wattens",
                                "bet_type": "3 Way",
                                "pick": "Home",
                                "odds": "1.34"
                            }
                        ),
                    ]
                ),
                lx.data.ExampleData(
                    text=textwrap.dedent("""\
                        TOTAL ODDS: 32.83
                        BET AMOUNT (KSH): 100.00
                        POSSIBLE WIN KSH 3,411.18"""),
                    extractions=[
                        lx.data.Extraction(
                            extraction_class="bet_summary",
                            extraction_text="TOTAL ODDS: 32.83",
                            attributes={
                                "total_odds": "32.83",
                                "bet_amount": "100.00",
                                "currency": "KSH",
                                "possible_win": "3,411.18"
                            }
                        ),
                    ]
                )
            ]

            # Extract structured data using LangExtract
            result = lx.extract(
                text_or_documents=ocr_text,
                prompt_description=prompt,
                examples=examples,
                model_id="gemini-2.5-flash",
                extraction_passes=1,      # Single pass - OCR text is clean
                max_workers=5,
                max_char_buffer=5000
            )

            logger.info(f"LangExtract extracted {len(result.extractions)} entities")

            # Filter matches and summaries
            matches = [e for e in result.extractions
                      if e.extraction_class == "match"
                      and e.extraction_text
                      and e.extraction_text != "null"]
            bet_summaries = [e for e in result.extractions
                            if e.extraction_class == "bet_summary"]

            logger.info(f"Found {len(matches)} valid matches and {len(bet_summaries)} bet summaries")

            return {
                'success': True,
                'langextract_result': result,
                'matches': matches,
                'bet_summaries': bet_summaries,
                'ocr_text': ocr_text,
                'text_blocks': []  # Not used for langextract
            }

        except ImportError as e:
            logger.error(f"Missing library for Gemini+LangExtract: {str(e)}")
            return {
                'success': False,
                'error': 'LangExtract or google-genai is not installed. Please contact administrator.',
                'text_blocks': []
            }
        except Exception as e:
            logger.error(f"Gemini+LangExtract extraction failed: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to extract using Gemini+LangExtract: {str(e)}',
                'text_blocks': []
            }

    def _preprocess_image(self, image_path, strategy='light'):
        """
        Preprocess image to improve OCR accuracy

        Args:
            image_path: Path to the image file
            strategy: 'none', 'light', 'medium', or 'heavy'
        """
        try:
            # Import cv2 here to avoid import errors if not installed
            import cv2
            import numpy as np

            # Read image
            img = cv2.imread(image_path)

            if img is None:
                logger.warning(f"Could not preprocess image, using original")
                return image_path

            # No preprocessing - just return original
            if strategy == 'none':
                logger.info("Using original image without preprocessing")
                return image_path

            # Convert to grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

            if strategy == 'light':
                # Light preprocessing: Just grayscale + slight sharpening
                logger.info("Applying light preprocessing (grayscale + sharpening)")

                # Sharpen the image slightly
                kernel = np.array([[-1,-1,-1],
                                   [-1, 9,-1],
                                   [-1,-1,-1]])
                processed = cv2.filter2D(gray, -1, kernel)

            elif strategy == 'medium':
                # Medium preprocessing: Grayscale + contrast enhancement
                logger.info("Applying medium preprocessing (grayscale + contrast)")

                # Apply CLAHE for contrast enhancement
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                processed = clahe.apply(gray)

            else:  # heavy
                # Heavy preprocessing: Full pipeline (original aggressive method)
                logger.info("Applying heavy preprocessing (full pipeline)")

                # Apply noise reduction
                denoised = cv2.medianBlur(gray, 3)

                # Increase contrast
                clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
                contrast_enhanced = clahe.apply(denoised)

                # Thresholding
                _, processed = cv2.threshold(contrast_enhanced, 0, 255,
                                            cv2.THRESH_BINARY + cv2.THRESH_OTSU)

            # Save processed image
            base_name = os.path.basename(image_path)
            image_dir = os.path.dirname(image_path)
            processed_path = os.path.join(image_dir, f"processed_{strategy}_{base_name}")
            cv2.imwrite(processed_path, processed)

            logger.info(f"Saved preprocessed image to: {processed_path}")
            return processed_path

        except ImportError:
            logger.warning("OpenCV is not installed, skipping image preprocessing")
            return image_path
        except Exception as e:
            logger.warning(f"Image preprocessing failed: {e}, using original image")
            return image_path
    
    def parse_betslip(self, text_blocks):
        """Parse extracted text to identify betting information"""
        logger.info("Starting betslip parsing")

        all_text = ' '.join([block['text'] for block in text_blocks])
        logger.debug(f"Full extracted text: {all_text[:200]}...")  # Log first 200 chars

        bet_code = self._extract_bet_code(all_text)
        total_odds = self._extract_total_odds(all_text)
        possible_win = self._extract_possible_win(all_text)
        matches = self._extract_matches(text_blocks)
        confidence = self._calculate_confidence(text_blocks)
        expires_at = self._estimate_expiry_time(text_blocks)

        logger.info(f"Parsed results - Bet code: {bet_code}, Odds: {total_odds}, "
                   f"Possible Win: {possible_win}, Matches found: {len(matches)}, "
                   f"Confidence: {confidence:.2f}%")

        # Validate cumulative odds
        odds_validation = self._validate_cumulative_odds(matches, total_odds)

        # Convert datetime objects to ISO format strings for JSON serialization
        result = {
            'bet_code': bet_code,
            'total_odds': total_odds,
            'possible_win': possible_win,
            'matches': matches,
            'confidence': confidence,
            'expires_at': expires_at.isoformat() if expires_at else None,
            'odds_validation': odds_validation  # Add validation results
        }

        return result
    
    def _extract_bet_code(self, text):
        """Extract bet code from text"""
        # Common bet code patterns (including Kenyan bookmakers)
        patterns = [
            # General patterns
            r'CODE[:\s]+([A-Z0-9]+)',
            r'Bet\s+Code[:\s]+([A-Z0-9]+)',
            r'Booking\s+Code[:\s]+([A-Z0-9]+)',
            r'Reference[:\s]+([A-Z0-9]+)',
            r'Slip\s+ID[:\s]+([A-Z0-9]+)',

            # SportPesa patterns
            r'Betslip\s+ID[:\s]+([A-Z0-9]+)',
            r'ID[:\s]+([A-Z0-9]{8,})',

            # Betika patterns
            r'(\d{10,12})',  # Betika codes are usually 10-12 digits

            # Mozzartbet patterns
            r'Ticket[:\s]+([A-Z0-9]+)',
            r'Coupon[:\s]+([A-Z0-9]+)',

            # Generic patterns
            r'\b([A-Z]{2,3}\d{6,})\b',  # Common format: XX123456 or XXX123456
            r'\b([A-Z]\d{7,})\b',  # Single letter + numbers
            r'\b(\d{8,})\b'  # Pure numbers
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                code = match.group(1)
                # Filter out obvious non-bet-codes (like dates)
                if len(code) >= 6 and not re.match(r'^\d{1,2}[/-]\d{1,2}', code):
                    return code

        return None
    
    def _extract_total_odds(self, text):
        """Extract total odds from text"""
        patterns = [
            r'Total\s+Odds[:\s]+([\d,]+\.?\d*)',
            r'Total[:\s]+([\d,]+\.?\d*)',
            r'Odds[:\s]+([\d,]+\.?\d*)',
            r'@\s*([\d,]+\.?\d*)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                odds_str = match.group(1).replace(',', '')
                try:
                    odds_value = float(odds_str)
                    # Validate odds are in reasonable range (1.01 to 9999.99)
                    if 1.01 <= odds_value <= 9999.99:
                        return odds_value
                except ValueError:
                    continue

        return None

    def _extract_possible_win(self, text):
        """Extract possible win amount from text"""
        patterns = [
            r'Possible\s+Win[:\s]+KSH\s*([\d,]+\.?\d*)',
            r'Possible\s+Win[:\s]+([\d,]+\.?\d*)',
            r'Total\s+Win[:\s]+KSH\s*([\d,]+\.?\d*)',
            r'Win[:\s]+KSH\s*([\d,]+\.?\d*)'
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                win_str = match.group(1).replace(',', '')
                try:
                    return float(win_str)
                except ValueError:
                    continue

        return None
    
    def _extract_matches(self, text_blocks):
        """Extract individual matches and betting markets"""
        matches = []
        current_match = {}
        i = 0

        while i < len(text_blocks):
            text = text_blocks[i]['text'].strip()

            # Try to identify team names (using – or - separator)
            teams = self._extract_teams(text)

            # If no separator found, check if this and next block could be team names
            if not teams and i + 1 < len(text_blocks):
                next_text = text_blocks[i + 1]['text'].strip()

                # Check if both lines look like team names
                if self._looks_like_team_name(text) and self._looks_like_team_name(next_text):
                    # Clean team names
                    home_team = re.sub(r'^[#\s_\-]+|[#\s_\-]+$', '', text).strip()
                    away_team = re.sub(r'^[#\s_\-]+|[#\s_\-]+$', '', next_text).strip()

                    if len(home_team) >= 3 and len(away_team) >= 3:
                        teams = [home_team, away_team]
                        logger.debug(f"Found consecutive team names: {home_team} vs {away_team}")
                        i += 1  # Skip the next block since we used it as away team

            if teams:
                # Validate team names - skip if they are ONLY market keywords
                # (prevents "Number of Goals - Full Time" from being treated as teams)
                # But allow real team names that happen to contain these words (e.g., "Total Network Solutions FC")
                market_only_pattern = r'^(number\s+of|total|goals?|score|full\s+time|half\s+time|first\s+half|second\s+half|correct\s+score|over|under)[\s\-]*$'
                home_is_market_only = re.search(market_only_pattern, teams[0].strip(), re.IGNORECASE)
                away_is_market_only = re.search(market_only_pattern, teams[1].strip() if len(teams) > 1 else '', re.IGNORECASE)

                # Skip if either team is ONLY market keywords (not a real team name)
                if home_is_market_only or away_is_market_only:
                    logger.debug(f"Skipping line with market-only keywords: {text}")
                    i += 1
                    continue
                # Start new potential match
                potential_match = {
                    'home_team': teams[0],
                    'away_team': teams[1] if len(teams) > 1 else 'Unknown',
                    'league': self._extract_league(text),
                    'market': None,
                    'selection': None,
                    'odds': None,
                    'match_date': None
                }

                # Look ahead for market type, pick, and odds using DYNAMIC structure-based approach
                j = i + 1
                found_pick = False
                found_odds = False
                lines_scanned = []

                while j < len(text_blocks) and j < i + 8:  # Look up to 8 lines ahead
                    next_text = text_blocks[j]['text'].strip()
                    lines_scanned.append(next_text)

                    # DYNAMIC MARKET DETECTION: If no market yet, capture first non-team line as market
                    # Market is typically the first line after teams (could be anything)
                    if not potential_match['market'] and not self._is_pick_line(next_text) and not self._is_odds_only(next_text):
                        # Don't capture if it's obviously teams or pure noise
                        if not self._extract_teams(next_text) and len(next_text) >= 3:
                            potential_match['market'] = next_text
                            logger.debug(f"Dynamic market detected: {next_text}")

                    # DYNAMIC PICK DETECTION: Check for explicit "Pick:" prefix first
                    pick_match = re.search(r'(?:Your\s+)?Pick[:\s]+(.+)', next_text, re.IGNORECASE)
                    if pick_match:
                        selection = pick_match.group(1).strip()
                        # Clean up the selection (remove trailing punctuation and odds)
                        selection = re.sub(r'\s*\d{1,3}\.\d{2}$', '', selection)  # Remove trailing odds
                        selection = re.sub(r'[,;.!?]+$', '', selection).strip()
                        potential_match['selection'] = selection
                        found_pick = True
                        logger.debug(f"Found explicit pick: {selection}")

                    # DYNAMIC PICK DETECTION: If no explicit pick prefix, look for pick after market
                    # Pick is usually 1-2 lines after market, before odds
                    if not found_pick and potential_match['market'] and not self._is_odds_only(next_text):
                        # Skip if this line looks like another team pair or market descriptor
                        if not self._extract_teams(next_text) and len(next_text) >= 1:
                            # Check if this could be a selection (not just pure numbers)
                            if re.search(r'[a-zA-Z]', next_text):
                                # This could be a pick - capture it
                                selection = next_text.strip()
                                # Remove odds if embedded
                                selection = re.sub(r'\s*\d{1,3}\.\d{2}$', '', selection).strip()
                                if len(selection) >= 1 and selection.lower() not in ['pick', 'your pick', 'selection']:
                                    potential_match['selection'] = selection
                                    found_pick = True
                                    logger.debug(f"Dynamic pick detected: {selection}")

                    # ODDS DETECTION: Always look for decimal odds (most reliable pattern)
                    odds_match = re.search(r'\b(\d{1,3}\.\d{2})\b', next_text)
                    if odds_match and not potential_match['odds']:
                        odds_value = float(odds_match.group(1))
                        # Validate odds range
                        if 1.01 <= odds_value <= 999.99:
                            potential_match['odds'] = odds_value
                            found_odds = True
                            logger.debug(f"Found odds: {odds_value}")
                            # Once we have odds, continue scanning 1-2 more lines for pick if missing
                            if found_pick:
                                break

                    j += 1

                # Only add match if we found both pick AND odds (validates it's a real match)
                if found_pick and found_odds:
                    # Save previous match if exists
                    if current_match and current_match.get('odds'):
                        matches.append(current_match)

                    # Set default market if not found
                    if not potential_match['market']:
                        potential_match['market'] = '3 Way'

                    # Estimate match date
                    potential_match['match_date'] = self._estimate_match_date().isoformat()

                    current_match = potential_match
                else:
                    # This wasn't a valid match, skip it
                    logger.debug(f"Skipping potential match (no pick/odds): {teams[0]} vs {teams[1]}")

            i += 1

        # Add last match if valid
        if current_match and current_match.get('odds'):
            matches.append(current_match)

        return matches
    
    def _extract_teams(self, text):
        """Extract team names from text line"""
        # Look for various team separator patterns
        # Note: \u2013 is em dash (–), \u2014 is en dash (—)
        vs_patterns = [
            r'(.+?)\s+[\u2013\u2014\-]\s+(.+)',  # em dash, en dash, or hyphen separator
            r'(.+?)\s+(?:vs?\.?|versus)\s+(.+)',  # vs, v., versus
            r'(.+?)\s+/\s+(.+)',  # slash separator
            r'(.+?)\s+@\s+(.+)',  # @ separator (away @ home)
            r'(.+?)\s+x\s+(.+)',  # x separator (common in some bookmakers)
        ]

        for pattern in vs_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                home_team = match.group(1).strip()
                away_team = match.group(2).strip()

                # Remove common prefixes/suffixes
                home_team = re.sub(r'^(Home|Away|H|A)[:\s]+', '', home_team, flags=re.IGNORECASE)
                away_team = re.sub(r'^(Home|Away|H|A)[:\s]+', '', away_team, flags=re.IGNORECASE)

                # Clean up team names - remove special chars but keep letters, numbers, spaces, &
                home_team = re.sub(r'[^\w\s&]', '', home_team).strip()
                away_team = re.sub(r'[^\w\s&]', '', away_team).strip()

                # Remove trailing numbers (odds) if present
                home_team = re.sub(r'\s+\d+\.?\d*$', '', home_team).strip()
                away_team = re.sub(r'\s+\d+\.?\d*$', '', away_team).strip()

                # Validate team names (at least 3 characters each, not too long)
                if (len(home_team) >= 3 and len(away_team) >= 3 and
                    len(home_team) <= 50 and len(away_team) <= 50):
                    return [home_team, away_team]

        return None

    def _looks_like_team_name(self, text):
        """Check if text looks like a team name (no keywords, reasonable length)"""
        # Clean the text first
        cleaned = re.sub(r'^[#\s_\-]+|[#\s_\-]+$', '', text).strip()

        # Must have reasonable length
        if len(cleaned) < 3 or len(cleaned) > 50:
            return False

        # Shouldn't be just numbers or odds
        if re.match(r'^\d+\.?\d*$', cleaned):
            return False

        # Shouldn't contain betting keywords
        betting_keywords = r'\b(pick|your|share|multi\s+bet|total\s+odds|possible\s+win|ksh|win|bet\s+amount|excise)\b'
        if re.search(betting_keywords, cleaned, re.IGNORECASE):
            return False

        # Shouldn't contain market types - but be more lenient
        # Only reject if it's ONLY market keywords, not if it has team names + market keywords
        market_only = r'^(over|under|btts|goals?|score|way|double\s+chance|total|full\s+time)[\s\-]*$'
        if re.search(market_only, cleaned, re.IGNORECASE):
            return False

        # Should contain letters (team names have letters)
        if not re.search(r'[a-zA-Z]{2,}', cleaned):
            return False

        return True

    def _is_pick_line(self, text):
        """Check if text explicitly contains 'Pick:' or 'Your Pick:' prefix"""
        return bool(re.search(r'(?:Your\s+)?Pick[:\s]+', text, re.IGNORECASE))

    def _is_odds_only(self, text):
        """Check if text is just odds (a decimal number)"""
        # Check if text is just a decimal odds value (possibly with whitespace)
        return bool(re.match(r'^\s*\d{1,3}\.\d{2}\s*$', text.strip()))

    def _extract_market(self, text):
        """Extract betting market information"""
        # Use fuzzy matching to identify markets
        best_match = process.extractOne(text, self.common_markets, scorer=fuzz.partial_ratio)
        
        if best_match and best_match[1] > 70:  # 70% confidence threshold
            market = best_match[0]
            
            # Extract odds
            odds_match = re.search(r'([\d,]+\.?\d*)', text)
            odds = float(odds_match.group(1).replace(',', '')) if odds_match else None
            
            # Extract selection (simplified)
            selection = text.replace(market, '').strip()
            selection = re.sub(r'[\d,]+\.?\d*', '', selection).strip()
            
            return {
                'market': market,
                'selection': selection or market,
                'odds': odds
            }
        
        return None
    
    def _extract_league(self, text):
        """Extract league/competition name"""
        # Common league patterns (including Kenyan and African leagues)
        leagues = [
            # English Football
            'Premier League', 'EPL', 'English Premier League', 'Championship',
            'League One', 'League Two', 'FA Cup', 'EFL Cup', 'Carabao Cup',

            # European Leagues
            'La Liga', 'Serie A', 'Bundesliga', 'Ligue 1', 'Eredivisie',
            'Primeira Liga', 'Scottish Premiership', 'Belgian Pro League',

            # European Competitions
            'Champions League', 'UEFA Champions League', 'UCL',
            'Europa League', 'UEFA Europa League', 'UEL',
            'Europa Conference League', 'Conference League',

            # Kenyan & East African
            'Kenya Premier League', 'KPL', 'FKF Premier League',
            'FKF Cup', 'Kenyan Premier League',
            'Tanzania Premier League', 'Uganda Premier League',

            # African Competitions
            'CAF Champions League', 'AFCON', 'Africa Cup of Nations',
            'CAF Confederation Cup', 'CHAN',

            # International
            'World Cup', 'FIFA World Cup', 'EURO', 'UEFA EURO',
            'Copa America', 'Nations League',

            # Other Major Leagues
            'MLS', 'Major League Soccer', 'Liga MX',
            'Brazilian Serie A', 'Argentine Primera',
            'Saudi Pro League', 'J-League'
        ]

        best_match = process.extractOne(text, leagues, scorer=fuzz.partial_ratio)
        if best_match and best_match[1] > 75:  # Lowered threshold for better matching
            return best_match[0]

        return 'Unknown League'
    
    def _extract_match_date(self, text):
        """Extract match date/time"""
        # Try to find date patterns
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
            r'(\d{1,2}\s+[A-Za-z]{3}\s+\d{2,4})',
            r'(Today|Tomorrow|Mon|Tue|Wed|Thu|Fri|Sat|Sun)'
        ]

        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                # For simplicity, set to tomorrow for now
                # In production, implement proper date parsing
                return timezone.now() + timedelta(days=1)

        # Default to tomorrow if no date found
        return timezone.now() + timedelta(days=1)

    def _estimate_match_date(self):
        """Estimate match date - defaults to tomorrow"""
        return timezone.now() + timedelta(days=1)
    
    def _calculate_confidence(self, text_blocks):
        """Calculate overall OCR confidence score"""
        if not text_blocks:
            return 0.0
        
        total_confidence = sum(block['confidence'] for block in text_blocks)
        return total_confidence / len(text_blocks)
    
    def _estimate_expiry_time(self, text_blocks):
        """Estimate when the tip should expire based on match times"""
        # For now, set expiry to 24 hours from now
        # In production, calculate based on actual match times
        return timezone.now() + timedelta(hours=24)

    def _validate_cumulative_odds(self, matches, total_odds):
        """
        Validate that cumulative odds (product of all match odds) matches total odds

        Returns:
            dict: {
                'is_valid': bool,
                'calculated_odds': float,
                'extracted_odds': float,
                'difference': float,
                'difference_percentage': float,
                'message': str
            }
        """
        if not matches:
            return {
                'is_valid': False,
                'calculated_odds': None,
                'extracted_odds': total_odds,
                'difference': None,
                'difference_percentage': None,
                'message': 'No matches found to calculate cumulative odds'
            }

        # Calculate cumulative odds (multiply all match odds)
        calculated_odds = 1.0
        missing_odds_count = 0

        for match in matches:
            if match.get('odds') is not None and match['odds'] > 0:
                calculated_odds *= match['odds']
            else:
                missing_odds_count += 1

        # Check if we have all odds
        if missing_odds_count > 0:
            logger.warning(f"Missing odds for {missing_odds_count} match(es)")
            return {
                'is_valid': False,
                'calculated_odds': calculated_odds,
                'extracted_odds': total_odds,
                'difference': None,
                'difference_percentage': None,
                'message': f'Missing odds for {missing_odds_count} match(es). Cannot validate cumulative odds.'
            }

        # Round to 2 decimal places for comparison
        calculated_odds = round(calculated_odds, 2)

        # Check if total odds was extracted
        if total_odds is None or total_odds <= 0:
            logger.warning("Total odds not extracted or invalid")
            return {
                'is_valid': False,
                'calculated_odds': calculated_odds,
                'extracted_odds': total_odds,
                'difference': None,
                'difference_percentage': None,
                'message': 'Total odds not extracted from betslip. Please verify manually.'
            }

        # Calculate difference
        difference = abs(calculated_odds - total_odds)
        difference_percentage = (difference / total_odds) * 100 if total_odds > 0 else 0

        # Tolerance: Allow up to 5% difference (accounts for rounding and OCR errors)
        tolerance_percentage = 5.0
        is_valid = difference_percentage <= tolerance_percentage

        # Log validation result
        if is_valid:
            logger.info(f"✓ Odds validation PASSED: Calculated={calculated_odds}, Extracted={total_odds}, "
                       f"Difference={difference:.2f} ({difference_percentage:.2f}%)")
        else:
            logger.warning(f"✗ Odds validation FAILED: Calculated={calculated_odds}, Extracted={total_odds}, "
                          f"Difference={difference:.2f} ({difference_percentage:.2f}%)")

        return {
            'is_valid': is_valid,
            'calculated_odds': calculated_odds,
            'extracted_odds': total_odds,
            'difference': round(difference, 2),
            'difference_percentage': round(difference_percentage, 2),
            'message': (
                f'✓ Odds match (difference: {difference_percentage:.1f}%)' if is_valid
                else f'⚠ Odds mismatch detected! Calculated: {calculated_odds}, Extracted: {total_odds} '
                     f'(difference: {difference_percentage:.1f}%). Please verify manually.'
            )
        }

    def _process_langextract_result(self, extraction_result):
        """
        Process LangExtract extraction result and convert to expected format.

        Args:
            extraction_result: Dictionary containing langextract_result, matches, and bet_summaries

        Returns:
            Dictionary in expected parsed_data format
        """
        matches = extraction_result.get('matches', [])
        bet_summaries = extraction_result.get('bet_summaries', [])

        # Extract bet code from OCR text (look for common patterns)
        ocr_text = extraction_result.get('ocr_text', '')
        bet_code = self._extract_bet_code(ocr_text) or 'UNKNOWN'

        # Process matches
        parsed_matches = []
        for match in matches:
            attrs = match.attributes or {}

            # Parse odds
            odds_str = attrs.get('odds', '0.0')
            try:
                odds = float(str(odds_str).replace(',', ''))
            except (ValueError, AttributeError):
                odds = 0.0

            parsed_matches.append({
                'home_team': attrs.get('home_team', 'Unknown'),
                'away_team': attrs.get('away_team', 'Unknown'),
                'league': 'Unknown League',
                'market': attrs.get('bet_type', 'Unknown'),
                'selection': attrs.get('pick', 'Unknown'),
                'odds': odds,
                'match_date': self._estimate_match_date().isoformat()
            })

        # Extract summary data
        total_odds = 0.0
        possible_win = 0.0
        bet_amount = 0.0
        currency = 'KSH'

        for summary in bet_summaries:
            attrs = summary.attributes or {}

            if 'total_odds' in attrs:
                try:
                    total_odds = float(str(attrs['total_odds']).replace(',', ''))
                except (ValueError, AttributeError):
                    pass

            if 'possible_win' in attrs:
                try:
                    possible_win = float(str(attrs['possible_win']).replace(',', ''))
                except (ValueError, AttributeError):
                    pass

            if 'bet_amount' in attrs:
                try:
                    bet_amount = float(str(attrs['bet_amount']).replace(',', ''))
                except (ValueError, AttributeError):
                    pass

            if 'currency' in attrs:
                currency = attrs['currency']

        # Validate cumulative odds
        odds_validation = self._validate_cumulative_odds(parsed_matches, total_odds)

        # Build result
        parsed_data = {
            'bet_code': bet_code,
            'total_odds': total_odds,
            'possible_win': possible_win,
            'bet_amount': bet_amount,
            'currency': currency,
            'matches': parsed_matches,
            'confidence': 97.0,  # High confidence for LangExtract
            'expires_at': self._estimate_expiry_time([]).isoformat(),
            'odds_validation': odds_validation,
            'ocr_text': ocr_text  # Save OCR text for debugging
        }

        logger.info(f"LangExtract parsed results - Bet code: {bet_code}, Odds: {total_odds}, "
                   f"Possible Win: {possible_win}, Matches found: {len(parsed_matches)}, "
                   f"Confidence: 97.00%")

        return parsed_data

    def process_betslip_image(self, image_file):
        """Main method to process a betslip image"""
        try:
            # Read image file
            image_bytes = image_file.read()
            image_file.seek(0)  # Reset file pointer
            
            # Extract text using Textract
            extraction_result = self.extract_text_from_image(image_bytes)
            
            if not extraction_result['success']:
                return {
                    'success': False,
                    'error': extraction_result['error']
                }
            
            # --- LangExtract Handling (PRIORITY) ---
            if 'langextract_result' in extraction_result and extraction_result['langextract_result']:
                logger.info("Processing betslip using LangExtract structured data.")
                parsed_data = self._process_langextract_result(extraction_result)

            # --- Gemini Structured Data Handling ---
            elif 'gemini_structured_data' in extraction_result and extraction_result['gemini_structured_data']:
                gemini_data = extraction_result['gemini_structured_data']
                logger.info("Processing betslip using Gemini structured data.")

                # Map Gemini data to existing parsed_data structure
                parsed_matches = []
                for gm in gemini_data.get('matches', []):
                    parsed_matches.append({
                        'home_team': gm.get('home_team'),
                        'away_team': gm.get('away_team'),
                        'league': 'Unknown League',  # Default for now
                        'market': gm.get('bet_type', 'Unknown'),
                        'selection': gm.get('pick', 'Unknown'),
                        'odds': float(gm.get('odds', 0.0)) if gm.get('odds') else 0.0,
                        'match_date': self._estimate_match_date().isoformat()
                    })

                total_odds = float(gemini_data['summary']['total_odds'].replace(',', '')) if gemini_data.get('summary') and gemini_data['summary'].get('total_odds') else 0.0
                possible_win = float(gemini_data['summary']['possible_win'].replace(',', '')) if gemini_data.get('summary') and gemini_data['summary'].get('possible_win') else 0.0
                bet_code = gemini_data.get('bet_code', 'UNKNOWN')

                # Validate cumulative odds using the Gemini-extracted matches and total odds
                odds_validation = self._validate_cumulative_odds(parsed_matches, total_odds)

                parsed_data = {
                    'bet_code': bet_code,
                    'total_odds': total_odds,
                    'possible_win': possible_win,
                    'matches': parsed_matches,
                    'confidence': 99.0,  # High confidence for Gemini structured extraction
                    'expires_at': self._estimate_expiry_time([]).isoformat(),
                    'odds_validation': odds_validation
                }
                logger.info(f"Gemini parsed results - Bet code: {bet_code}, Odds: {total_odds}, "
                            f"Possible Win: {possible_win}, Matches found: {len(parsed_matches)}, "
                            f"Confidence: 99.00%")
            else:
                # Original parsing logic for other OCR providers
                parsed_data = self.parse_betslip(extraction_result['text_blocks'])
                logger.info("Processing betslip using traditional OCR text parsing.")

            return {
                'success': True,
                'data': parsed_data,
                'confidence': parsed_data['confidence']
            }

        except Exception as e:
            logger.error(f"Error in process_betslip_image: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to process image: {str(e)}'
            }

    async def _scrape_sportpesa_bet(self, url: str) -> dict:
        """
        Scrapes bet information from a SportPesa referral link using Playwright.

        Args:
            url: The SportPesa referral URL (e.g., https://www.ke.sportpesa.com/referral/MPCPYA)

        Returns:
            Dictionary containing bet information with matches, markets, odds, and picks
        """
        try:
            from playwright.async_api import async_playwright
        except ImportError:
            return {
                'error': 'Playwright is not installed. Please run: pip install playwright && playwright install chromium',
                'url': url,
                'scraped_at': datetime.now().isoformat()
            }

        try:
            async with async_playwright() as p:
                # Launch browser
                browser = await p.chromium.launch(headless=True)
                context = await browser.new_context(
                    viewport={'width': 1920, 'height': 1080},
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                )
                page = await context.new_page()

                try:
                    logger.info(f"Navigating to SportPesa URL: {url}")
                    await page.goto(url, wait_until='domcontentloaded', timeout=60000)

                    # Wait for JavaScript to execute
                    logger.info("Waiting for content to load...")
                    await asyncio.sleep(5)

                    # Extract bet information
                    logger.info("Extracting bet data...")
                    bet_data = {
                        'referral_code': url.split('/')[-1],
                        'scraped_at': datetime.now().isoformat(),
                        'matches': []
                    }

                    # Wait for betslip to load
                    try:
                        await page.wait_for_selector('.betslip-content-bet', timeout=10000)
                        logger.info("Betslip found!")
                    except Exception as e:
                        logger.error(f"Betslip not found: {e}")
                        return {
                            'error': 'No betslip found on this page',
                            'referral_code': url.split('/')[-1],
                            'scraped_at': datetime.now().isoformat()
                        }

                    # Find all bet items in the betslip
                    bet_elements = await page.query_selector_all('li.betslip-content-bet')
                    logger.info(f"Found {len(bet_elements)} bets in betslip")

                    for bet_element in bet_elements:
                        try:
                            # Extract teams
                            teams_elem = await bet_element.query_selector('.betslip-game-name, [data-qa="selection-event-description"]')
                            teams = await teams_elem.inner_text() if teams_elem else None

                            # Extract market
                            market_elem = await bet_element.query_selector('[data-qa="selection-market"]')
                            market = await market_elem.inner_text() if market_elem else None

                            # Extract pick
                            pick_elem = await bet_element.query_selector('.your-pick, [data-qa="selection-your-pick"]')
                            pick = await pick_elem.inner_text() if pick_elem else None

                            # Extract odds
                            odds_elem = await bet_element.query_selector('.betslip-bet-current-odd, [data-qa="selection-your-odd"]')
                            odds = await odds_elem.inner_text() if odds_elem else None

                            # Try to extract date (if available)
                            date_elem = await bet_element.query_selector('[class*="date"], [class*="time"], time')
                            date = await date_elem.inner_text() if date_elem else None

                            match_info = {
                                'teams': teams.strip() if teams else None,
                                'market': market.strip() if market else None,
                                'pick': pick.strip() if pick else None,
                                'odds': odds.strip() if odds else None,
                                'date': date.strip() if date else None,
                            }

                            bet_data['matches'].append(match_info)
                            logger.info(f"Extracted: {teams} - {market} - {pick} @ {odds}")

                        except Exception as e:
                            logger.error(f"Error extracting bet data: {e}")
                            continue

                    # Get total odds if available
                    try:
                        total_odds_elem = await page.query_selector('.betslip-total-odd, [data-qa*="total-odd"]')
                        if total_odds_elem:
                            bet_data['total_odds'] = await total_odds_elem.inner_text()
                    except Exception as e:
                        logger.error(f"Could not extract total odds: {e}")

                    return bet_data

                except Exception as e:
                    return {
                        'error': str(e),
                        'url': url,
                        'scraped_at': datetime.now().isoformat()
                    }
                finally:
                    await browser.close()

        except Exception as e:
            # Handle Playwright browser not installed or other launch errors
            error_msg = str(e)
            if "Executable doesn't exist" in error_msg or "ms-playwright" in error_msg:
                logger.error(
                    "Playwright browsers not installed. "
                    "Run 'playwright install chromium' in production to fix this. "
                    "Skipping SportPesa scraping."
                )
                return {
                    'error': 'Playwright browsers not installed. Please run: playwright install chromium',
                    'url': url,
                    'scraped_at': datetime.now().isoformat(),
                    'help': 'Contact admin to install Playwright browsers on the server'
                }
            else:
                logger.error(f"Failed to launch browser for SportPesa scraping: {error_msg}")
                return {
                    'error': f'Failed to launch browser: {error_msg}',
                    'url': url,
                    'scraped_at': datetime.now().isoformat()
                }

    def process_sportpesa_link(self, sharing_link: str):
        """
        Process a SportPesa bet sharing link and extract match information.

        Args:
            sharing_link: SportPesa referral/sharing URL

        Returns:
            Dictionary with success status and extracted data in OCR format
        """
        try:
            logger.info(f"Processing SportPesa link: {sharing_link}")

            # Run async scraper
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            scraped_data = loop.run_until_complete(self._scrape_sportpesa_bet(sharing_link))
            loop.close()

            # Check for errors
            if 'error' in scraped_data:
                return {
                    'success': False,
                    'error': scraped_data['error']
                }

            # Convert scraper format to OCR format
            parsed_data = self._convert_sportpesa_to_ocr_format(scraped_data)

            return {
                'success': True,
                'data': parsed_data,
                'confidence': 95.0  # High confidence since data comes directly from SportPesa
            }

        except Exception as e:
            logger.error(f"Failed to process SportPesa link: {str(e)}", exc_info=True)
            return {
                'success': False,
                'error': f'Failed to process SportPesa link: {str(e)}'
            }

    def _convert_sportpesa_to_ocr_format(self, scraped_data: dict) -> dict:
        """
        Convert SportPesa scraper output to OCR format for consistency.

        Args:
            scraped_data: Data from SportPesa scraper

        Returns:
            Dictionary in OCR format
        """
        matches = []
        total_odds = 1.0

        for match in scraped_data.get('matches', []):
            # Parse team names (format: "Team A – Team B")
            teams_str = match.get('teams', '')
            if '–' in teams_str:
                team_parts = teams_str.split('–')
                home_team = team_parts[0].strip()
                away_team = team_parts[1].strip() if len(team_parts) > 1 else ''
            elif ' - ' in teams_str:
                team_parts = teams_str.split(' - ')
                home_team = team_parts[0].strip()
                away_team = team_parts[1].strip() if len(team_parts) > 1 else ''
            elif ' vs ' in teams_str.lower():
                team_parts = teams_str.lower().split(' vs ')
                home_team = team_parts[0].strip().title()
                away_team = team_parts[1].strip().title() if len(team_parts) > 1 else ''
            else:
                home_team = teams_str
                away_team = ''

            # Parse odds
            odds_str = match.get('odds', '1.0')
            try:
                odds = float(odds_str)
                total_odds *= odds
            except (ValueError, TypeError):
                odds = 1.0

            # Build match object
            match_obj = {
                'home_team': home_team,
                'away_team': away_team,
                'league': 'SportPesa',  # Default league, will be Unknown League in DB
                'market': match.get('market', 'Unknown'),
                'selection': match.get('pick', 'Unknown'),
                'odds': odds,
                'match_date': match.get('date'),  # Usually null for referral links
            }

            matches.append(match_obj)

        # Use scraped total odds if available, otherwise use calculated
        if 'total_odds' in scraped_data:
            try:
                total_odds = float(scraped_data['total_odds'])
            except (ValueError, TypeError):
                pass

        return {
            'bet_code': scraped_data.get('referral_code', 'UNKNOWN'),
            'total_odds': round(total_odds, 2),
            'matches': matches,
            'bookmaker': 'sportpesa',
            'confidence': 95.0,
            'scraped_at': scraped_data.get('scraped_at'),
        }