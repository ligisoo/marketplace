# Production Fix Summary - Playwright Browser Installation

## ✅ What Was Fixed

### Problem
The scheduler was crashing in production with:
```
Failed to process betslip: Executable doesn't exist at /home/ubuntu/.cache/ms-playwright/chromium-1105/chrome-linux/chrome
```

### Root Cause
Playwright browsers weren't installed on the production server. The `playwright` Python package was installed, but the actual browser binaries (Chromium) were not downloaded.

### Solution Applied

**1. Added Graceful Error Handling ✅**

Updated both scraping services to handle missing browsers gracefully instead of crashing:
- `apps/tips/services/livescore_scraper.py` - Won't crash if Chromium is missing
- `apps/tips/ocr.py` - SportPesa scraper won't crash if Chromium is missing

Now when browsers are missing:
- Error is logged clearly with instructions
- Service continues running (doesn't crash)
- Returns helpful error message to user
- Other scheduler jobs continue working

**2. Created Production Deployment Guide ✅**

Created `PLAYWRIGHT_PRODUCTION_FIX.md` with complete instructions for:
- Installing Playwright browsers
- Docker/container deployment
- Troubleshooting steps
- System dependency requirements

## 🚀 Action Required in Production

### Immediate Fix (Run in your production pod/server):

```bash
# SSH into production server
cd /path/to/your/marketplace

# Install Playwright browsers
playwright install chromium

# Or if you get command not found:
python -m playwright install chromium

# Install system dependencies (may need sudo)
playwright install-deps chromium
```

### Verify Installation:

```bash
# Test that it works
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); print('✓ OK'); browser.close(); p.stop()"
```

Should print `✓ OK` without errors.

### Restart Scheduler:

```bash
# If using systemd:
sudo systemctl restart tip-scheduler

# If using nohup:
pkill -f run_scheduler.py
nohup python run_scheduler.py > logs/scheduler.log 2>&1 &
```

## 📊 What Happens Now

###Before Fix:
- ❌ Scheduler crashes when trying to scrape
- ❌ Service restarts infinitely (40+ restarts)
- ❌ No tips processed

### After Installing Browsers:
- ✅ Livescore scraping works
- ✅ SportPesa scraping works
- ✅ Result verification runs successfully
- ✅ Temp tip cleanup runs successfully
- ✅ Service stays running

### If You Don't Install Browsers (with our code fixes):
- ⚠️ Scheduler keeps running (doesn't crash)
- ⚠️ Scraping is skipped with helpful error messages
- ⚠️ Manual verification still works
- ⚠️ Other features continue working
- ✅ Service stays up

## 📝 Files Changed

1. **apps/tips/services/livescore_scraper.py** - Added try/except for browser launch
2. **apps/tips/ocr.py** - Added try/except for SportPesa scraper browser launch
3. **PLAYWRIGHT_PRODUCTION_FIX.md** - Complete installation guide (NEW)
4. **POD_DEPLOYMENT_DEBUG.md** - General deployment debugging guide (NEW)
5. **PRODUCTION_FIX_SUMMARY.md** - This file (NEW)

## 🔍 How to Check If Fixed

### Check Service Status:
```bash
# Should show "active (running)" not restarting
sudo systemctl status tip-scheduler
```

### Check Logs:
```bash
# Should NOT see browser executable errors
tail -f logs/tip_scheduler.log

# If browsers not yet installed, you'll see:
# "Playwright browsers not installed. Run 'playwright install chromium' to fix."

# After installing browsers, you'll see:
# "Scraping livescore from: https://www.livescore.com/en/football/live/"
# "Found X matches"
```

### Test Manually:
```bash
cd /path/to/marketplace
python test_scheduler.py
```

Should complete without errors about missing browsers.

## 📦 Storage Requirements

- Chromium browser: ~100-150 MB
- System dependencies: ~100-200 MB
- Total: ~200-350 MB

Make sure your production environment has enough disk space.

## 🐳 Docker/Container Notes

If using Docker, add to your `Dockerfile`:
```dockerfile
RUN pip install playwright==1.42.0
RUN playwright install chromium
RUN playwright install-deps chromium
```

Or use Playwright's official Docker image:
```dockerfile
FROM mcr.microsoft.com/playwright/python:v1.42.0-focal
```

See `PLAYWRIGHT_PRODUCTION_FIX.md` for detailed Docker instructions.

## ✅ Deployment Checklist

- [ ] SSH into production server
- [ ] Navigate to project directory
- [ ] Run `playwright install chromium`
- [ ] Run `playwright install-deps chromium` (if needed)
- [ ] Test installation: `python -c "from playwright.sync_api import ..."`
- [ ] Restart scheduler service
- [ ] Monitor logs for 5-10 minutes
- [ ] Verify no more browser errors
- [ ] Confirm scraping is working

## 📚 Documentation

- **PLAYWRIGHT_PRODUCTION_FIX.md** - Full installation guide
- **POD_DEPLOYMENT_DEBUG.md** - General deployment troubleshooting
- **DEPLOYMENT_GUIDE.md** - Complete deployment guide with scheduler setup
- **QUICKSTART_SCHEDULER.md** - Quick start for scheduler

## 🆘 Still Having Issues?

1. Check logs: `tail -f logs/tip_scheduler.log`
2. Run manually: `python run_scheduler.py`
3. Check `POD_DEPLOYMENT_DEBUG.md` for common issues
4. Ensure you're using the correct Python path in production
5. Verify database is accessible from production environment

## Summary

- ✅ Code fixed - scheduler won't crash anymore
- ⚠️ Still need to install browsers in production for full functionality
- 📖 Complete documentation provided
- 🚀 One command to fix: `playwright install chromium`
