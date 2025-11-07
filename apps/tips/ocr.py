import boto3
import json
import re
import logging
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
            
            # Parse the extracted text
            parsed_data = self.parse_betslip(extraction_result['text_blocks'])
            
            return {
                'success': True,
                'data': parsed_data,
                'confidence': parsed_data['confidence']
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Failed to process image: {str(e)}'
            }