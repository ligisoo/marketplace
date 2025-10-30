import boto3
import json
import re
import logging
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from fuzzywuzzy import fuzz, process

# Set up logging
logger = logging.getLogger(__name__)


class BetslipOCR:
    """OCR service for extracting betting information from betslip screenshots"""
    
    def __init__(self):
        self.textract = boto3.client(
            'textract',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        )
        
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
    
    def parse_betslip(self, text_blocks):
        """Parse extracted text to identify betting information"""
        logger.info("Starting betslip parsing")

        all_text = ' '.join([block['text'] for block in text_blocks])
        logger.debug(f"Full extracted text: {all_text[:200]}...")  # Log first 200 chars

        bet_code = self._extract_bet_code(all_text)
        total_odds = self._extract_total_odds(all_text)
        matches = self._extract_matches(text_blocks)
        confidence = self._calculate_confidence(text_blocks)
        expires_at = self._estimate_expiry_time(text_blocks)

        logger.info(f"Parsed results - Bet code: {bet_code}, Odds: {total_odds}, "
                   f"Matches found: {len(matches)}, Confidence: {confidence:.2f}%")

        # Convert datetime objects to ISO format strings for JSON serialization
        result = {
            'bet_code': bet_code,
            'total_odds': total_odds,
            'matches': matches,
            'confidence': confidence,
            'expires_at': expires_at.isoformat() if expires_at else None
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
            r'Odds[:\s]+([\d,]+\.?\d*)',
            r'@\s*([\d,]+\.?\d*)',
            r'Total[:\s]+([\d,]+\.?\d*)'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                odds_str = match.group(1).replace(',', '')
                try:
                    return float(odds_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_matches(self, text_blocks):
        """Extract individual matches and betting markets"""
        matches = []
        current_match = {}
        
        for block in text_blocks:
            text = block['text'].strip()
            
            # Skip common headers/footers
            if any(keyword in text.lower() for keyword in ['betslip', 'total', 'code', 'amount', 'balance']):
                continue
            
            # Try to identify team names
            teams = self._extract_teams(text)
            if teams:
                if current_match:
                    matches.append(current_match)

                match_date = self._extract_match_date(text)
                current_match = {
                    'home_team': teams[0],
                    'away_team': teams[1] if len(teams) > 1 else 'Unknown',
                    'league': self._extract_league(text),
                    'market': None,
                    'selection': None,
                    'odds': None,
                    'match_date': match_date.isoformat() if match_date else None
                }
            
            # Try to identify betting market
            market = self._extract_market(text)
            if market and current_match:
                current_match['market'] = market['market']
                current_match['selection'] = market['selection']
                current_match['odds'] = market['odds']
        
        if current_match:
            matches.append(current_match)
        
        return matches
    
    def _extract_teams(self, text):
        """Extract team names from text line"""
        # Look for various team separator patterns
        vs_patterns = [
            r'(.+?)\s+(?:vs?\.?|versus)\s+(.+)',  # vs, v., versus
            r'(.+?)\s+-\s+(.+)',  # dash separator
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

                # Clean up team names - remove special chars but keep letters, numbers, spaces
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