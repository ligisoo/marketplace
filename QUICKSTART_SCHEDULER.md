# Quick Start: Tip Scheduler with Python `schedule`

## ✅ What Was Done

Converted the tip result verification system from cron jobs to Python's `schedule` library.

## 📦 Files Created

1. **run_scheduler.py** - Main scheduler daemon (runs every 30 minutes by default)
2. **tip-scheduler.service** - Systemd service configuration
3. **test_scheduler.py** - Quick test script
4. **logs/** - Directory for scheduler logs

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
Scheduler is running. Press Ctrl+C to stop.
```

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
    # Change this line to your preferred schedule:

    # Every 30 minutes (default)
    schedule.every(30).minutes.do(run_result_verification)

    # OR Every hour
    # schedule.every().hour.do(run_result_verification)

    # OR Specific times
    # schedule.every().day.at("22:00").do(run_result_verification)
    # schedule.every().day.at("00:00").do(run_result_verification)
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
python test_scheduler.py
```

## 📊 What Gets Logged

Every run logs:
- Tips checked
- Tips verified
- Tips won/lost
- Matches found/not found
- Any errors

Check logs:
```bash
tail -f logs/tip_scheduler.log
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
