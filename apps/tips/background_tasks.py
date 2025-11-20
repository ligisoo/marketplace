"""
Background tasks for betslip processing and enrichment
"""
import logging
import hashlib
import copy
from typing import Optional
from django.utils import timezone
from django.core.cache import cache

from .models import Tip, TipMatch, OCRProviderSettings
from .betslip_extractor import process_betslip_image
from .enrichment_service import DataEnrichmentService

logger = logging.getLogger(__name__)


def get_file_hash(file_data: bytes) -> str:
    """Generate MD5 hash of file for caching (from langextract)"""
    return hashlib.md5(file_data).hexdigest()


def process_betslip_async(tip_id: int):
    """
    Background task to process betslip (OCR/scraping + enrichment)

    Args:
        tip_id: ID of the Tip to process
    """
    try:
        logger.info(f"Starting background processing for Tip {tip_id}")

        # Get tip
        tip = Tip.objects.get(id=tip_id)

        # Update status to processing
        tip.processing_status = 'processing'
        tip.save(update_fields=['processing_status', 'updated_at'])

        # Step 1: OCR/Scraping (if not already done)
        if not tip.ocr_processed:
            logger.info(f"Processing betslip data for Tip {tip_id}")

            if not tip.screenshot:
                raise ValueError("No screenshot available for processing")

            # Read screenshot data for hashing
            tip.screenshot.seek(0)
            file_data = tip.screenshot.read()
            tip.screenshot.seek(0)  # Reset for processing

            # Check cache first (MD5 hash-based caching from langextract)
            file_hash = get_file_hash(file_data)
            cache_key = f'betslip_{file_hash}'

            cached_result = cache.get(cache_key)
            if cached_result:
                logger.info(f"✓ Cache hit for Tip {tip_id}! Using cached extraction result.")
                ocr_result = copy.deepcopy(cached_result)
                ocr_result['cached'] = True
            else:
                logger.info(f"Cache miss for Tip {tip_id}. Processing with Gemini...")

                # Process screenshot with new fast extractor
                ocr_result = process_betslip_image(tip.screenshot)

                # Cache successful results for 24 hours (86400 seconds)
                if ocr_result.get('success'):
                    cache.set(cache_key, ocr_result, 86400)
                    logger.info(f"✓ Cached extraction result for future use")

            # Check if processing was successful
            if not ocr_result or not ocr_result.get('success'):
                error_msg = ocr_result.get('error', 'Unknown error') if ocr_result else 'Processing failed'
                raise ValueError(f"Extraction failed: {error_msg}")

            # Extract data from result
            match_data = ocr_result['data']
            confidence = ocr_result.get('confidence', 95.0)

            # Update tip with OCR data
            tip.match_details = match_data
            tip.ocr_processed = True
            tip.ocr_confidence = confidence

            # Extract bet code and odds if not set
            if tip.bet_code.startswith('TEMP_'):
                tip.bet_code = match_data.get('bet_code', tip.bet_code)

            if not tip.odds or tip.odds == 0:
                tip.odds = match_data.get('total_odds', 1.00)

            tip.save()

            if ocr_result.get('cached'):
                logger.info(f"OCR processing complete for Tip {tip_id} (from cache)")
            else:
                logger.info(f"OCR processing complete for Tip {tip_id}")

        # Step 2: Create TipMatch records (if not already created)
        existing_matches = TipMatch.objects.filter(tip=tip).count()
        if existing_matches == 0:
            logger.info(f"Creating TipMatch records for Tip {tip_id}")

            from datetime import timedelta
            matches = tip.match_details.get('matches', [])

            for match_data in matches:
                # Try to get match date from data, otherwise use a default
                match_date = match_data.get('match_date')
                if not match_date:
                    # Default to tomorrow if no date provided (will be updated by enrichment)
                    match_date = timezone.now() + timedelta(days=1)

                TipMatch.objects.create(
                    tip=tip,
                    home_team=match_data.get('home_team', ''),
                    away_team=match_data.get('away_team', ''),
                    league=match_data.get('league', 'Unknown'),
                    match_date=match_date,
                    market=match_data.get('market', ''),
                    selection=match_data.get('selection', ''),
                    odds=match_data.get('odds', 1.00)
                )

            logger.info(f"Created {len(matches)} TipMatch records for Tip {tip_id}")

            # Generate preview data for buyers (show first 2 matches)
            preview_matches = matches[:2]
            tip.preview_data = {
                'matches': [
                    {
                        'home_team': match.get('home_team', ''),
                        'away_team': match.get('away_team', ''),
                        'league': match.get('league', 'Unknown'),
                        'market': match.get('market', ''),
                    }
                    for match in preview_matches
                ],
                'total_matches': len(matches)
            }
            tip.save(update_fields=['preview_data', 'updated_at'])
            logger.info(f"Generated preview data for {len(preview_matches)} matches")

        # Step 3: Data Enrichment with API-Football
        logger.info(f"Starting API-Football enrichment for Tip {tip_id}")

        enrichment_service = DataEnrichmentService()
        tip_matches = TipMatch.objects.filter(tip=tip)

        # Enrich tip matches
        stats = enrichment_service.fetch_and_enrich(
            tip_matches.all(),
            fetch_fixtures=True
        )

        logger.info(f"Enrichment stats for Tip {tip_id}: {stats}")

        # Update preview data with enriched team names
        tip_matches_list = list(tip_matches.all()[:2])  # Get first 2 matches
        if tip_matches_list:
            tip.preview_data = {
                'matches': [
                    {
                        'home_team': match.home_team,
                        'away_team': match.away_team,
                        'league': match.league,
                        'market': match.market,
                    }
                    for match in tip_matches_list
                ],
                'total_matches': tip_matches.count()
            }
            logger.info(f"Updated preview data with enriched team names")

        # Update expires_at to the last match start time
        latest_match = tip_matches.order_by('-match_date').first()
        if latest_match:
            tip.expires_at = latest_match.match_date
            logger.info(f"Updated expires_at to {tip.expires_at} (last match time)")

        # Mark enrichment as complete
        tip.enrichment_completed = True
        tip.processing_status = 'completed'
        tip.save(update_fields=['enrichment_completed', 'processing_status', 'preview_data', 'expires_at', 'updated_at'])

        logger.info(f"Background processing completed successfully for Tip {tip_id}")

    except Exception as e:
        logger.error(f"Background processing failed for Tip {tip_id}: {str(e)}", exc_info=True)

        # Update tip with error
        try:
            tip = Tip.objects.get(id=tip_id)
            tip.processing_status = 'failed'
            tip.processing_error = str(e)
            tip.save(update_fields=['processing_status', 'processing_error', 'updated_at'])
        except Exception as save_error:
            logger.error(f"Failed to save error status: {str(save_error)}")


def processing_callback(task_id: str, result: Optional[any], error: Optional[Exception]):
    """
    Callback function for background task completion

    Args:
        task_id: Task ID
        result: Result of the task (None for this task)
        error: Exception if task failed, None otherwise
    """
    if error:
        logger.error(f"Task {task_id} failed: {str(error)}")
    else:
        logger.info(f"Task {task_id} completed successfully")
