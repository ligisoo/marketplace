# Quick Start: Tip Scheduler with Python `schedule`

## ✅ What Was Done

Converted scheduled jobs from cron to Python's `schedule` library:
1. **Tip Result Verification** - Verifies expired tips using livescore data (every 30 minutes)
2. **Temp Tip Cleanup** - Removes abandoned temporary tip submissions (every hour)

## 📦 Files Created

1. **run_scheduler.py** - Main scheduler daemon with both jobs
2. **tip-scheduler.service** - Systemd service configuration
3. **test_scheduler.py** - Test result verification
4. **test_cleanup.py** - Test temp tip cleanup
5. **logs/** - Directory for scheduler logs

## 🚀 Quick Start (3 Steps)

### Step 1: Test the Scheduler Manually

```bash
# Test it works
python test_scheduler.py

# Run scheduler in foreground (Ctrl+C to stop)
python run_scheduler.py
```

You should see:
```
============================================================
TIP RESULT VERIFICATION SCHEDULER STARTING
Started at: 2025-11-08 10:00:00
============================================================
Scheduler configured with the following jobs:
  - Job(interval=30, unit=minutes, do=run_result_verification, args=(), kwargs={})
  - Job(interval=1, unit=hours, do=cleanup_temp_tips, args=(), kwargs={})
Scheduler is running. Press Ctrl+C to stop.
```

## 📋 Scheduled Jobs

### Job 1: Result Verification (Every 30 minutes)
- Finds expired, unverified tips
- Scrapes livescore.com for match results
- Matches tip teams to livescore teams using fuzzy matching
- Determines if bets won/lost based on market type
- Updates database with results

### Job 2: Temp Tip Cleanup (Every hour)
- Finds temporary tips (bet_code starting with "TEMP_")
- Deletes tips older than 1 hour
- Cleans up abandoned submissions from tipsters who didn't complete the process

### Step 2: Install as System Service (Production)

```bash
# Install service
sudo cp tip-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tip-scheduler
sudo systemctl start tip-scheduler

# Check it's running
sudo systemctl status tip-scheduler
```

### Step 3: Monitor Logs

```bash
# View logs
tail -f logs/tip_scheduler.log

# Or use systemd journal
sudo journalctl -u tip-scheduler -f
```

## ⚙️ Customizing the Schedule

Edit `run_scheduler.py` in the `schedule_jobs()` function:

```python
def schedule_jobs():
    # Job 1: Result verification (default: every 30 minutes)
    schedule.every(30).minutes.do(run_result_verification)

    # Job 2: Temp tip cleanup (default: every hour)
    schedule.every().hour.do(cleanup_temp_tips)

    # Change schedules as needed:

    # Result verification alternatives:
    # schedule.every().hour.do(run_result_verification)  # Every hour
    # schedule.every().day.at("22:00").do(run_result_verification)  # Daily at 10pm

    # Cleanup alternatives:
    # schedule.every(30).minutes.do(cleanup_temp_tips)  # Every 30 minutes
    # schedule.every(2).hours.do(cleanup_temp_tips)  # Every 2 hours
```

After editing, restart:
```bash
sudo systemctl restart tip-scheduler
```

## 🎛️ Service Management

```bash
# Start
sudo systemctl start tip-scheduler

# Stop
sudo systemctl stop tip-scheduler

# Restart
sudo systemctl restart tip-scheduler

# Status
sudo systemctl status tip-scheduler

# View logs
sudo journalctl -u tip-scheduler -n 50
```

## 🔍 Troubleshooting

**Service won't start?**
```bash
# Run manually to see error
python run_scheduler.py
```

**No tips being verified?**
- This is normal if there are no expired tips with available match results
- Check database: `python manage.py shell`
  ```python
  from apps.tips.models import Tip
  from django.utils import timezone

  # Tips waiting for verification
  pending = Tip.objects.filter(
      status='active',
      is_resulted=False,
      expires_at__lt=timezone.now()
  )
  print(f"Pending: {pending.count()}")
  ```

**Want to test immediately?**
```bash
# Test result verification
python test_scheduler.py

# Test temp tip cleanup
python test_cleanup.py

# Run manual cleanup
python manage.py cleanup_temp_tips
```

## 📊 What Gets Logged

**Result Verification runs log:**
- Tips checked
- Tips verified
- Tips won/lost
- Matches found/not found
- Any errors

**Cleanup runs log:**
- Number of temp tips found
- Number of temp tips deleted
- Details of deleted tips (bet codes and age)

Check logs:
```bash
tail -f logs/tip_scheduler.log
```

Sample log output:
```
============================================================
SCHEDULED RESULT VERIFICATION STARTED
Time: 2025-11-08 22:00:00
============================================================
VERIFICATION STATS:
  Tips checked: 15
  Tips verified: 12
  ...
============================================================

============================================================
TEMP TIP CLEANUP STARTED
Time: 2025-11-08 23:00:00
============================================================
Found 3 temporary tip(s) to delete
  - TEMP_abc123 (age: 2.5h)
  - TEMP_def456 (age: 1.8h)
  - TEMP_ghi789 (age: 1.2h)
✓ Successfully deleted 3 temporary tip(s)
============================================================
```

## 🆚 Advantages Over Cron

✅ Easier to configure (Python code vs cron syntax)
✅ Better error handling and logging
✅ Can run manually for testing
✅ Automatic restarts with systemd
✅ Platform independent
✅ More flexible scheduling options

## 📚 Full Documentation

- **DEPLOYMENT_GUIDE.md** - Complete deployment guide
- **LIVESCORE_AUTO_VERIFICATION.md** - Technical documentation
- **test_livescore_verification.py** - Full test suite

## ⚡ TL;DR

```bash
# Test it
python run_scheduler.py

# Deploy it
sudo cp tip-scheduler.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable tip-scheduler
sudo systemctl start tip-scheduler

# Monitor it
tail -f logs/tip_scheduler.log
```

Done! 🎉
