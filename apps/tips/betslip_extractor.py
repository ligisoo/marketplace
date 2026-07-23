"""
Fast betslip extraction - Strictly following /home/walter/langextract/betslip_fast_extractor.py
Uses only libraries from langextract: google-genai, Pillow, python-dotenv
"""
import os
import json
import time
import io
import logging
from dotenv import load_dotenv
from PIL import Image
import google.genai as genai
from google.genai import types
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
load_dotenv()

# --- CONFIGURATION FOR SPEED (from langextract) ---
MODEL_ID = 'gemini-3.1-flash-lite'
MAX_DIMENSION = 800   # 800px is the sweet spot for speed/readability
JPEG_QUALITY = 60     # Lower quality (60) is fine for high-contrast text
RETRY_DELAY = 1.0     # Start retries quicker

# Initialize Client ONCE (Global Scope) to save setup time
api_key = os.getenv('GEMINI_API_KEY')
if not api_key:
    logger.error("No API key found. Set GEMINI_API_KEY in your .env file")

client = genai.Client(api_key=api_key) if api_key else None


# --- PYDANTIC SCHEMAS FOR STRUCTURED OUTPUT ---
class Match(BaseModel):
    match_date: str = Field(description="Date of the match (e.g. DD/MM/YY or DD/MM/YYYY). Must be empty string if date is not explicitly shown on the slip.")
    match_time: str = Field(description="Kickoff time (e.g. HH:MM). Must be empty string if time is not explicitly shown.")
    home_team: str
    away_team: str
    bet_type: str = Field(description="Betting market or type (e.g. 3 Way, Over/Under)")
    pick: str = Field(description="The user's pick or selection")
    odds: float = Field(description="The multiplier/odds for this selection")

class PredictionSlipSummary(BaseModel):
    total_odds: float = Field(description="The total multiplier/odds for the entire slip")

class PredictionSlip(BaseModel):
    is_placed_slip: bool = Field(description="True ONLY if the screenshot is a PLACED bet slip from bet history containing match dates/times for each selection. False if it is an unplaced draft or bet builder selection without match dates.")
    matches: list[Match]
    summary: PredictionSlipSummary


def _optimize_image_turbo(image_path_or_bytes) -> tuple[bytes, str]:
    """
    Aggressive optimization: Grayscale + Resize + Low Q JPEG
    (Exactly from langextract/betslip_fast_extractor.py)
    """
    try:
        # Handle both file path and bytes
        if isinstance(image_path_or_bytes, bytes):
            img = Image.open(io.BytesIO(image_path_or_bytes))
        else:
            img = Image.open(image_path_or_bytes)

        # 1. Convert to Grayscale ('L').
        # This removes color data, reducing payload size by ~66%.
        img = img.convert('L')

        # 2. Resize if larger than limit
        if max(img.size) > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION), Image.Resampling.LANCZOS)

        # 3. Save to buffer with lower quality
        buffer = io.BytesIO()
        img.save(buffer, format='JPEG', quality=JPEG_QUALITY, optimize=False)
        return buffer.getvalue(), 'image/jpeg'
    except Exception as e:
        raise ValueError(f"Image processing failed: {e}")


def extract_betslip_turbo(image_path_or_bytes) -> dict:
    """
    Fast betslip extraction (Exactly from langextract/betslip_fast_extractor.py)

    Args:
        image_path_or_bytes: Path to image file or bytes

    Returns:
        dict: {"success": bool, "data": dict} or {"success": False, "error": str}
    """
    start_total = time.time()

    if not client:
        return {"success": False, "error": "API client not initialized. Check API key."}

    # 1. Prepare Image (CPU Bound - very fast)
    try:
        image_data, mime_type = _optimize_image_turbo(image_path_or_bytes)
    except Exception as e:
        return {"success": False, "error": str(e)}

    # 2. Optimized Prompt
    prompt = (
        "Analyze this prediction slip image and extract match details.\n"
        "STRICT VALIDATION RULES:\n"
        "1. Set is_placed_slip to FALSE if the image contains 'BET AMOUNT', 'POSSIBLE WIN', '- / +' buttons, 'LIVE MULTI BET', or lacks explicit match dates/times for each selection.\n"
        "2. Set is_placed_slip to TRUE ONLY if this image is a placed bet history statement containing explicit dates (e.g. DD/MM/YY HH:MM) for every match.\n"
        "3. For match_date: extract ONLY the date string printed on that match row (e.g. '23/07/26'). If no date is printed for a match, set match_date to an empty string \"\"."
    )

    # 3. API Call
    max_retries = 2
    result_dict = None

    for attempt in range(max_retries):
        try:
            t_req_start = time.time()
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[prompt, types.Part.from_bytes(data=image_data, mime_type=mime_type)],
                config=types.GenerateContentConfig(
                    temperature=0.0, # Deterministic = usually faster caching
                    response_mime_type='application/json',
                    response_schema=PredictionSlip,
                )
            )
            # Response is parsed into Pydantic model automatically if SDK supports it,
            # but we can fallback to json.loads if .parsed isn't populated
            if hasattr(response, 'parsed') and response.parsed:
                result_dict = response.parsed.model_dump()
            else:
                result_dict = json.loads(response.text)
                
            logger.info(f"API Call Time: {time.time() - t_req_start:.2f}s")
            break
        except Exception as e:
            logger.warning(f"Retry {attempt+1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                return {"success": False, "error": f"Extraction failed: {str(e)}"}

    if not result_dict:
        return {"success": False, "error": "Failed to parse API response"}

    # 4. Fast Parsing & Math Check
    # Quick Math Validation
    if 'matches' in result_dict:
        calc_odds = 1.0
        for m in result_dict['matches']:
            # robust float conversion
            try:
                o = float(str(m.get('odds', 1)).replace(',', ''))
                calc_odds *= o
            except:
                pass

        # Add our calc to result for comparison
        if 'summary' not in result_dict or not result_dict['summary']:
            result_dict['summary'] = {}
        result_dict['summary']['calc_odds'] = round(calc_odds, 2)

    total_time = time.time() - start_total
    logger.info(f"Total extraction time: {total_time:.2f}s")

    return {"success": True, "data": result_dict}



def process_betslip_image(image_file) -> dict:
    """
    Django-compatible wrapper for extract_betslip_turbo
    Maintains compatibility with existing background_tasks.py

    Args:
        image_file: Django UploadedFile or file-like object

    Returns:
        dict: Compatible with existing OCR interface
    """
    try:
        # Read image bytes
        if hasattr(image_file, 'read'):
            image_bytes = image_file.read()
            image_file.seek(0)  # Reset file pointer
        else:
            image_bytes = image_file

        # Extract using turbo method
        result = extract_betslip_turbo(image_bytes)

        if not result['success']:
            return result

        # Convert to expected format for background_tasks.py
        betslip_data = result['data']
        is_placed = betslip_data.get('is_placed_slip', False)
        matches = betslip_data.get('matches', [])

        # Validate that the slip is a PLACED bet slip containing match dates/times
        missing_dates = False
        if not matches:
            missing_dates = True
        else:
            for m in matches:
                d_str = str(m.get('match_date') or '').strip()
                if not d_str:
                    missing_dates = True
                    break

        if not is_placed or missing_dates:
            return {
                'success': False,
                'error': (
                    "Invalid Prediction Slip: The uploaded image is missing match kickoff dates and times. "
                    "Please upload a prediction slip screenshot from your account history that clearly displays match dates and kickoff times."
                )
            }

        # Format matches
        formatted_matches = []
        for match in betslip_data.get('matches', []):
            formatted_matches.append({
                'home_team': match.get('home_team', 'Unknown'),
                'away_team': match.get('away_team', 'Unknown'),
                'league': 'Unknown League',  # Will be enriched later
                'market': match.get('bet_type', '3 Way'),
                'selection': match.get('pick', 'Unknown'),
                'odds': float(match.get('odds', 1.0)),
                'match_date': match.get('match_date'),
                'match_time': match.get('match_time'),
            })

        # Extract summary
        summary = betslip_data.get('summary', {})
        total_odds = summary.get('calc_odds', summary.get('total_odds', 1.0))

        return {
            'success': True,
            'data': {
                'bet_code': 'EXTRACTED',  # Will be updated by user
                'total_odds': float(total_odds),
                'matches': formatted_matches,
                'confidence': 95.0,
                'num_matches': len(formatted_matches)
            },
            'confidence': 95.0
        }

    except Exception as e:
        logger.error(f"Error in process_betslip_image: {str(e)}", exc_info=True)
        return {
            'success': False,
            'error': f'Failed to process image: {str(e)}'
        }
