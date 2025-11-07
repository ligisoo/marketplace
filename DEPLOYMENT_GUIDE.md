# Livescore Auto-Verification Deployment Guide

## Overview

This guide covers deploying the automated tip result verification system to production.

## Prerequisites

✅ All tests passing (`python test_livescore_verification.py`)
✅ Playwright browsers installed
✅ Required dependencies in requirements.txt

## Installation Steps

### 1. Install Playwright Browsers

```bash
cd /home/walter/marketplace
playwright install chromium
```

This installs the Chromium browser that Playwright uses for web scraping.

### 2. Verify Installation

Run a quick test to ensure everything works:

```bash
python manage.py verify_tip_results
```

Expected output:
```
============================================================
VERIFICATION COMPLETE
============================================================
Tips checked:        X
Tips verified:       X
Tips WON:            X
Tips LOST:           X
Tips pending:        X
Matches verified:    X
Matches not found:   X
============================================================
```

## Setting Up Cron Jobs

### Option 1: Every 30 Minutes (Recommended)

This catches matches as soon as they finish.

```bash
crontab -e
```

Add this line:
```
*/30 * * * * cd /home/walter/marketplace && /usr/bin/python3 manage.py schedule_result_verification >> /var/log/tip_verification.log 2>&1
```

### Option 2: Strategic Times Only

Run at times when most matches finish (less frequent, lower resource usage):

```
0 22 * * * cd /home/walter/marketplace && /usr/bin/python3 manage.py schedule_result_verification >> /var/log/tip_verification.log 2>&1
0 0 * * * cd /home/walter/marketplace && /usr/bin/python3 manage.py schedule_result_verification >> /var/log/tip_verification.log 2>&1
```

This runs at 10 PM and midnight daily.

### Option 3: Hourly

Balanced approach:

```
0 * * * * cd /home/walter/marketplace && /usr/bin/python3 manage.py schedule_result_verification >> /var/log/tip_verification.log 2>&1
```

## Cron Setup Steps

1. **Find your Python path:**
   ```bash
   which python3
   ```
   Use this path in the cron command (replace `/usr/bin/python3`)

2. **Create log directory:**
   ```bash
   sudo mkdir -p /var/log
   sudo touch /var/log/tip_verification.log
   sudo chmod 666 /var/log/tip_verification.log
   ```

3. **Edit crontab:**
   ```bash
   crontab -e
   ```

4. **Add your chosen schedule** (paste one of the options above)

5. **Save and exit** (Ctrl+X, then Y, then Enter in nano)

6. **Verify cron is set:**
   ```bash
   crontab -l
   ```

## Manual Verification

You can always trigger verification manually:

```bash
# Verify today's tips
python manage.py verify_tip_results

# Verify specific date
python manage.py verify_tip_results --date 2025-11-07
```

## Monitoring

### View Logs

```bash
# Live monitoring
tail -f /var/log/tip_verification.log

# View last 50 lines
tail -n 50 /var/log/tip_verification.log

# Search for errors
grep ERROR /var/log/tip_verification.log
```

### What to Look For

**Successful run:**
```
============================================================
SCHEDULED RESULT VERIFICATION STARTED
Time: 2025-11-08 22:00:00
============================================================
VERIFICATION STATS:
  Tips checked: 15
  Tips verified: 12
  Tips WON: 8
  Tips LOST: 4
  Tips pending: 3
  Matches verified: 45
  Matches not found: 3
✓ Verified 12 tips (8 won, 4 lost)
============================================================
SCHEDULED RESULT VERIFICATION COMPLETED
============================================================
```

**Warning signs:**
```
⚠️ No livescore match found for: Team A vs Team B
⚠️ Match Team A vs Team B not yet finished
```
These are normal - just means matches haven't finished yet or team names don't match perfectly.

**Error signs:**
```
❌ Error during scheduled verification: ...
ERROR: Exception occurred
```
These need investigation - check the full error message.

## Database Checks

### Check Verified Tips

```bash
python manage.py shell
```

```python
from apps.tips.models import Tip
from django.utils import timezone

# Recent verified tips
verified = Tip.objects.filter(is_resulted=True).order_by('-result_verified_at')[:10]
for tip in verified:
    print(f"Tip {tip.id}: {'WON' if tip.is_won else 'LOST'} - Verified at {tip.result_verified_at}")

# Tips waiting for results
pending = Tip.objects.filter(
    status='active',
    is_resulted=False,
    expires_at__lt=timezone.now()
)
print(f"\nPending verification: {pending.count()} tips")
```

### Check TipMatch Results

```python
from apps.tips.models import TipMatch

# Recently verified matches
matches = TipMatch.objects.filter(is_resulted=True).order_by('-id')[:10]
for m in matches:
    print(f"{m.home_team} vs {m.away_team}: {m.actual_result} - {'WON' if m.is_won else 'LOST'}")
```

## Performance Considerations

### Resource Usage

Each verification run:
- Takes ~10-15 seconds
- Opens one browser instance
- Scrapes one page from livescore.com
- Updates database records

### Recommendations

**Small-scale (< 50 tips/day):**
- Run every 30 minutes ✅
- Minimal resource impact

**Medium-scale (50-200 tips/day):**
- Run every hour ✅
- Consider rate limiting

**Large-scale (200+ tips/day):**
- Run at strategic times (10pm, midnight) ✅
- Consider implementing caching
- Monitor livescore.com access

## Troubleshooting

### Cron Not Running

1. **Check cron service:**
   ```bash
   sudo service cron status
   sudo service cron restart
   ```

2. **Check cron logs:**
   ```bash
   grep CRON /var/log/syslog
   ```

3. **Test command directly:**
   ```bash
   cd /home/walter/marketplace && python manage.py schedule_result_verification
   ```

### Browser Not Found

If you see: `Error: Playwright browser not found`

```bash
cd /home/walter/marketplace
playwright install chromium
```

### Team Names Not Matching

If matches consistently show as "not found":

1. Check actual team names in livescore.com
2. Add abbreviation to `livescore_scraper.py`:

```python
abbreviations = {
    'man utd': 'manchester united',
    'new_abbreviation': 'full_name',  # Add here
}
```

### No Matches Found

If no matches are found even though they exist:

1. **Check livescore.com structure:**
   ```bash
   python manage.py shell
   ```
   ```python
   from apps.tips.services import LivescoreScraper
   scraper = LivescoreScraper()
   matches = scraper.scrape_live_scores_sync()
   print(f"Found {len(matches)} matches")
   for m in matches[:3]:
       print(m)
   ```

2. **Check if HTML structure changed:**
   - Visit https://www.livescore.com/en/football/live/
   - View page source
   - Compare with `livescore_scraper.py` selectors

## Backup Strategy

Before deploying:

```bash
# Backup database
python manage.py dumpdata tips > backup_tips_$(date +%Y%m%d).json

# Backup crontab
crontab -l > backup_crontab_$(date +%Y%m%d).txt
```

## Rollback Plan

If verification causes issues:

1. **Stop cron:**
   ```bash
   crontab -e
   # Comment out the verification line with #
   ```

2. **Revert database (if needed):**
   ```bash
   python manage.py loaddata backup_tips_YYYYMMDD.json
   ```

## Production Checklist

Before going live:

- [ ] All tests passing (`python test_livescore_verification.py`)
- [ ] Playwright browsers installed (`playwright install chromium`)
- [ ] Cron job configured and tested
- [ ] Log file created and writable
- [ ] Database backup taken
- [ ] Manual verification tested successfully
- [ ] Monitoring dashboard set up (optional)
- [ ] Error alerting configured (optional)

## Next Steps

1. **Monitor for 24-48 hours** - Watch logs closely
2. **Verify accuracy** - Check a few tips manually
3. **Adjust schedule if needed** - Based on match times
4. **Add more abbreviations** - As you discover team name variations

## Support

For issues or questions:
1. Check logs: `tail -f /var/log/tip_verification.log`
2. Run test script: `python test_livescore_verification.py`
3. Review documentation: `LIVESCORE_AUTO_VERIFICATION.md`

## Additional Resources

- **livescore_scraper.py** - Scraping logic
- **result_verifier.py** - Verification logic
- **LIVESCORE_AUTO_VERIFICATION.md** - Technical documentation
- **test_livescore_verification.py** - Test suite
