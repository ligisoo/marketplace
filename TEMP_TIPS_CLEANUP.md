# Temporary Tips Cleanup

## Problem

Every time a user uploaded a betslip but didn't complete the verification form, a temporary Tip record was left in the database with a bet_code like `TEMP_1762373112480632`.

These abandoned submissions accumulated over time because they were only deleted if:
1. OCR processing failed
2. User completed the verification form

## Solution

### 1. Automatic Cleanup (apps/tips/views.py:150-156)

Added automatic cleanup in the `create_tip` view that runs every time the tip creation page loads:

```python
# Clean up old temporary tips (older than 1 hour)
from datetime import timedelta
one_hour_ago = timezone.now() - timedelta(hours=1)
Tip.objects.filter(
    bet_code__startswith='TEMP_',
    created_at__lt=one_hour_ago
).delete()
```

**When it runs**: Every time someone visits the "Create Tip" page

**What it deletes**: All TEMP_ tips older than 1 hour

### 2. Management Command

Created a Django management command for manual cleanup or scheduled cron jobs:

**Location**: `apps/tips/management/commands/cleanup_temp_tips.py`

**Usage**:

```bash
# Dry run (see what would be deleted)
python manage.py cleanup_temp_tips --dry-run

# Actually delete (default: older than 1 hour)
python manage.py cleanup_temp_tips

# Custom age threshold
python manage.py cleanup_temp_tips --hours 24

# Dry run with custom threshold
python manage.py cleanup_temp_tips --hours 12 --dry-run
```

**Options**:
- `--hours N`: Delete tips older than N hours (default: 1)
- `--dry-run`: Show what would be deleted without actually deleting

### 3. Initial Cleanup

Cleaned up 6 existing temporary tips:
- `TEMP_1762373788172821` (11.2 hours old)
- `TEMP_1762373319058985` (11.4 hours old)
- `TEMP_1762373112480632` (11.4 hours old)
- `TEMP_1762372490032852` (11.6 hours old)
- `TEMP_1761927056761174` (135.3 hours old - 5.6 days!)
- 1 more

All have been deleted from the database.

## Future Maintenance

### Option 1: Automatic (Recommended)
The automatic cleanup in `create_tip` view runs regularly as users create tips. No action needed.

### Option 2: Scheduled Task
Set up a cron job to run the cleanup command periodically:

```bash
# Run every hour
0 * * * * source venv/bin/activate && python manage.py cleanup_temp_tips

# Run daily at 2 AM
0 2 * * * cd /home/walter/marketplace && source venv/bin/activate && python manage.py cleanup_temp_tips --hours 24
```

## Monitoring

To check for temporary tips:

```bash
source venv/bin/activate
python manage.py shell -c "
from apps.tips.models import Tip
temp_count = Tip.objects.filter(bet_code__startswith='TEMP_').count()
print(f'Current temporary tips: {temp_count}')
"
```

## Why 1 Hour?

The 1-hour threshold was chosen because:
- ✅ Gives users time to complete verification if they're slow
- ✅ Prevents database bloat from abandoned submissions
- ✅ Doesn't interfere with legitimate in-progress submissions
- ✅ If a user takes > 1 hour, they can just re-upload (OCR data is lost anyway after that long)

## Impact

- **Database**: Cleaner, no accumulation of abandoned records
- **Performance**: Minimal overhead (simple query on indexed field)
- **User Experience**: No change - users can still take their time verifying
- **Storage**: Uploaded betslip images are also deleted with the tip record (Django's `FileField` cascade delete)

