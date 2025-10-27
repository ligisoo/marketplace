import boto3
import json
import re
from datetime import datetime, timedelta
from django.conf import settings
from django.utils import timezone
from fuzzywuzzy import fuzz, process


class BetslipOCR:
    """OCR service for extracting betting information from betslip screenshots"""
    
    def __init__(self):
        self.textract = boto3.client(
            'textract',
            aws_access_key_id=getattr(settings, 'AWS_ACCESS_KEY_ID', ''),
            aws_secret_access_key=getattr(settings, 'AWS_SECRET_ACCESS_KEY', ''),
            region_name=getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        )
        
        # Common betting markets for fuzzy matching
        self.common_markets = [
            'Over 2.5', 'Under 2.5', 'Over 1.5', 'Under 1.5', 'Over 3.5', 'Under 3.5',
            'Both Teams to Score', 'BTTS', 'GG', 'NG',
            '1X2', 'Match Result', 'Full Time Result',
            'Double Chance', '1X', 'X2', '12',
            'Correct Score', 'Half Time Result',
            'Total Goals', 'Asian Handicap'
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
            
            return {
                'success': True,
                'text_blocks': text_blocks,
                'raw_response': response
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'text_blocks': []
            }
    
    def parse_betslip(self, text_blocks):
        """Parse extracted text to identify betting information"""
        all_text = ' '.join([block['text'] for block in text_blocks])
        
        result = {
            'bet_code': self._extract_bet_code(all_text),
            'total_odds': self._extract_total_odds(all_text),
            'matches': self._extract_matches(text_blocks),
            'confidence': self._calculate_confidence(text_blocks),
            'expires_at': self._estimate_expiry_time(text_blocks)
        }
        
        return result
    
    def _extract_bet_code(self, text):
        """Extract bet code from text"""
        # Common bet code patterns
        patterns = [
            r'CODE[:\s]+([A-Z0-9]+)',
            r'Bet\s+Code[:\s]+([A-Z0-9]+)',
            r'Reference[:\s]+([A-Z0-9]+)',
            r'\b([A-Z]{2}\d{6,})\b',  # Common format: XX123456
            r'\b(\d{8,})\b'  # Pure numbers
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
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
                
                current_match = {
                    'home_team': teams[0],
                    'away_team': teams[1] if len(teams) > 1 else 'Unknown',
                    'league': self._extract_league(text),
                    'market': None,
                    'selection': None,
                    'odds': None,
                    'match_date': self._extract_match_date(text)
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
        # Look for vs, v, - patterns
        vs_patterns = [
            r'(.+?)\s+(?:vs?|v)\s+(.+)',
            r'(.+?)\s+-\s+(.+)',
            r'(.+?)\s+/\s+(.+)'
        ]
        
        for pattern in vs_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                home_team = match.group(1).strip()
                away_team = match.group(2).strip()
                
                # Clean up team names
                home_team = re.sub(r'[^\w\s]', '', home_team).strip()
                away_team = re.sub(r'[^\w\s]', '', away_team).strip()
                
                if len(home_team) > 2 and len(away_team) > 2:
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
        # Common league patterns
        leagues = [
            'Premier League', 'EPL', 'La Liga', 'Serie A', 'Bundesliga',
            'Champions League', 'Europa League', 'KPL', 'FKF',
            'World Cup', 'AFCON', 'EURO'
        ]
        
        best_match = process.extractOne(text, leagues, scorer=fuzz.partial_ratio)
        if best_match and best_match[1] > 80:
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