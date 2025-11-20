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

logger = logging.getLogger(__name__)
load_dotenv()

# --- CONFIGURATION FOR SPEED (from langextract) ---
MODEL_ID = 'gemini-2.5-flash-lite'
MAX_DIMENSION = 800   # 800px is the sweet spot for speed/readability
JPEG_QUALITY = 60     # Lower quality (60) is fine for high-contrast text
RETRY_DELAY = 1.0     # Start retries quicker

# Initialize Client ONCE (Global Scope) to save setup time
api_key = os.getenv('LANGEXTRACT_API_KEY')
if not api_key:
    logger.warning("LANGEXTRACT_API_KEY not found, trying GEMINI_API_KEY")
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        logger.error("No API key found. Set LANGEXTRACT_API_KEY or GEMINI_API_KEY")

client = genai.Client(api_key=api_key) if api_key else None


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

    # 2. Optimized Prompt (proper field names for compatibility)
    prompt = """Extract betslip as JSON:
{"matches":[{"match_date":"DD/MM/YY","match_time":"HH:MM","teams":"Home - Away","home_team":"Home","away_team":"Away","bet_type":"3 Way","pick":"Selection","odds":"1.50"}],"summary":{"total_odds":"10.50"}}

Extract ONLY matches. Use exact names. Output JSON only."""

    # 3. API Call
    max_retries = 2
    response_text = ""

    for attempt in range(max_retries):
        try:
            t_req_start = time.time()
            response = client.models.generate_content(
                model=MODEL_ID,
                contents=[prompt, types.Part.from_bytes(data=image_data, mime_type=mime_type)],
                config=types.GenerateContentConfig(
                    temperature=0.0, # Deterministic = usually faster caching
                    response_mime_type='application/json',
                    max_output_tokens=1024 # Lower token limit cuts off runaways
                )
            )
            response_text = response.text
            logger.info(f"API Call Time: {time.time() - t_req_start:.2f}s")
            break
        except Exception as e:
            logger.warning(f"Retry {attempt+1}/{max_retries}: {e}")
            if attempt < max_retries - 1:
                time.sleep(RETRY_DELAY)
            else:
                return {"success": False, "error": "API Timeout/RateLimit"}

    # 4. Fast Parsing & Math Check
    try:
        result = json.loads(response_text)

        # Quick Math Validation
        if 'matches' in result:
            calc_odds = 1.0
            for m in result['matches']:
                # robust float conversion
                try:
                    o = float(str(m.get('odds', 1)).replace(',', ''))
                    calc_odds *= o
                except:
                    pass

            # Add our calc to result for comparison
            if 'summary' not in result:
                result['summary'] = {}
            result['summary']['calc_odds'] = round(calc_odds, 2)

        total_time = time.time() - start_total
        logger.info(f"Total extraction time: {total_time:.2f}s")

        return {"success": True, "data": result}

    except json.JSONDecodeError:
        return {"success": False, "error": "Invalid JSON", "raw": response_text}


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
