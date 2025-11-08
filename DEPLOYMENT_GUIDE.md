# Livescore Auto-Verification Deployment Guide

## Overview

This guide covers deploying the automated tip result verification system using Python's `schedule` library instead of cron jobs.

## Prerequisites

✅ All tests passing (`python test_livescore_verification.py`)
✅ Playwright browsers installed
✅ Required dependencies in requirements.txt (including `schedule==1.2.2`)

## Installation Steps

### 1. Verify Installation

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

### 2. Create Log Files

```bash
sudo touch /var/log/tip_scheduler.log
sudo touch /var/log/tip_scheduler_error.log
sudo chown walter:walter /var/log/tip_scheduler.log
sudo chown walter:walter /var/log/tip_scheduler_error.log
```

## Deployment Options

### Option 1: Systemd Service (Recommended for Production)

This runs the scheduler as a system service that starts automatically on boot.

#### Step 1: Install the service

```bash
# Copy service file to systemd directory
sudo cp /home/walter/marketplace/tip-scheduler.service /etc/systemd/system/

# Reload systemd to recognize the new service
sudo systemctl daemon-reload

# Enable service to start on boot
sudo systemctl enable tip-scheduler

# Start the service
sudo systemctl start tip-scheduler
```

#### Step 2: Verify it's running

```bash
# Check service status
sudo systemctl status tip-scheduler

# View recent logs
sudo journalctl -u tip-scheduler -n 50 --no-pager

# Follow logs in real-time
sudo journalctl -u tip-scheduler -f
```

#### Managing the Service

```bash
# Start
sudo systemctl start tip-scheduler

# Stop
sudo systemctl stop tip-scheduler

# Restart
sudo systemctl restart tip-scheduler

# Check status
sudo systemctl status tip-scheduler

# Disable auto-start on boot
sudo systemctl disable tip-scheduler
```

### Option 2: Run Manually in Background (Development/Testing)

For testing or non-production environments:

```bash
# Run in foreground (see output, Ctrl+C to stop)
python run_scheduler.py

# Run in background
nohup python run_scheduler.py &

# Stop background process
pkill -f run_scheduler.py
```

### Option 3: Screen/Tmux Session

For servers where you want to easily attach/detach:

```bash
# Using screen
screen -S tip-scheduler
python run_scheduler.py
# Press Ctrl+A then D to detach
# screen -r tip-scheduler to reattach

# Using tmux
tmux new -s tip-scheduler
python run_scheduler.py
# Press Ctrl+B then D to detach
# tmux attach -t tip-scheduler to reattach
```

## Configuring the Schedule

Edit `/home/walter/marketplace/run_scheduler.py` to customize when verification runs:

```python
def schedule_jobs():
    # Default: Every 30 minutes
    schedule.every(30).minutes.do(run_result_verification)

    # Alternative schedules:

    # Every hour
    # schedule.every().hour.do(run_result_verification)

    # Every hour at :30 minutes past
    # schedule.every().hour.at(":30").do(run_result_verification)

    # Every day at specific times
    # schedule.every().day.at("22:00").do(run_result_verification)  # 10 PM
    # schedule.every().day.at("00:00").do(run_result_verification)  # Midnight

    # Every 2 hours
    # schedule.every(2).hours.do(run_result_verification)

    # Multiple times per day
    # schedule.every().day.at("10:00").do(run_result_verification)
    # schedule.every().day.at("14:00").do(run_result_verification)
    # schedule.every().day.at("18:00").do(run_result_verification)
    # schedule.every().day.at("22:00").do(run_result_verification)
```

After editing, restart the service:
```bash
sudo systemctl restart tip-scheduler
```

## Recommended Schedules

### Small-scale (< 50 tips/day)
```python
schedule.every(30).minutes.do(run_result_verification)
```
Catches matches quickly with minimal overhead.

### Medium-scale (50-200 tips/day)
```python
schedule.every().hour.do(run_result_verification)
```
Balanced approach.

### Large-scale (200+ tips/day)
```python
schedule.every().day.at("22:00").do(run_result_verification)
schedule.every().day.at("23:00").do(run_result_verification)
schedule.every().day.at("00:00").do(run_result_verification)
```
Strategic times when most matches finish.

## Manual Verification

You can still trigger verification manually anytime:

```bash
# Verify today's tips
python manage.py verify_tip_results

# Verify specific date
python manage.py verify_tip_results --date 2025-11-07
```

## Monitoring

### View Logs

```bash
# Using systemd journal (if using systemd)
sudo journalctl -u tip-scheduler -f

# Using log files directly
tail -f /var/log/tip_scheduler.log

# View errors
tail -f /var/log/tip_scheduler_error.log

# View last 100 lines
tail -n 100 /var/log/tip_scheduler.log

# Search for specific terms
grep "verified" /var/log/tip_scheduler.log
grep "ERROR" /var/log/tip_scheduler.log
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

**Healthy scheduler:**
```
TIP RESULT VERIFICATION SCHEDULER STARTING
Started at: 2025-11-08 10:00:00
Scheduler configured with the following jobs:
  - Every 30 minutes do run_result_verification()
Scheduler is running. Press Ctrl+C to stop.
```

## Database Checks

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

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status tip-scheduler

# View detailed logs
sudo journalctl -u tip-scheduler -n 100 --no-pager

# Check if Python path is correct
which python3

# Test script manually
python run_scheduler.py
```

### Common Issues

**1. Permission Denied on Log Files**
```bash
sudo chown walter:walter /var/log/tip_scheduler.log
sudo chown walter:walter /var/log/tip_scheduler_error.log
sudo chmod 664 /var/log/tip_scheduler.log
sudo chmod 664 /var/log/tip_scheduler_error.log
```

**2. Service Keeps Restarting**
```bash
# Check error logs
sudo journalctl -u tip-scheduler -n 50 --no-pager | grep ERROR

# Run script manually to see error
python run_scheduler.py
```

**3. Database Connection Issues**
Make sure PostgreSQL is running:
```bash
sudo systemctl status postgresql
```

**4. Import Errors**
Ensure virtual environment is activated in service file:
```bash
# Check service file has correct Python path
cat /etc/systemd/system/tip-scheduler.service | grep ExecStart
```

### Scheduler Not Running Tasks

```bash
# Check if scheduler loop is active
ps aux | grep run_scheduler

# View logs to see if jobs are scheduled
tail -n 20 /var/log/tip_scheduler.log

# Check system time is correct
date
```

## Performance Monitoring

### Resource Usage

Check scheduler resource consumption:

```bash
# CPU and memory usage
ps aux | grep run_scheduler

# Detailed stats (if running as systemd service)
systemctl status tip-scheduler
```

### Expected Resource Usage

- **CPU**: < 1% when idle, 5-10% during scraping
- **Memory**: 50-100 MB
- **Disk I/O**: Minimal (log writes only)
- **Network**: ~1 MB per scraping session

## Backup Strategy

Before deploying:

```bash
# Backup database
python manage.py dumpdata tips > backup_tips_$(date +%Y%m%d).json

# Backup scheduler configuration
cp run_scheduler.py run_scheduler.py.backup
```

## Rollback Plan

If scheduler causes issues:

```bash
# Stop the service
sudo systemctl stop tip-scheduler

# Disable auto-start
sudo systemctl disable tip-scheduler

# Restore database if needed
python manage.py loaddata backup_tips_YYYYMMDD.json
```

## Production Checklist

Before going live:

- [ ] All tests passing (`python test_livescore_verification.py`)
- [ ] Log files created with correct permissions
- [ ] Systemd service installed and enabled
- [ ] Service starts successfully (`sudo systemctl status tip-scheduler`)
- [ ] Database backup taken
- [ ] Manual verification tested successfully
- [ ] Logs show scheduler is running jobs at correct intervals
- [ ] Verified at least one automatic verification cycle

## Testing the Deployment

### Step-by-Step Test

1. **Test the script manually:**
   ```bash
   python run_scheduler.py
   ```
   Let it run for 1-2 minutes, then Ctrl+C. Check logs.

2. **Test as systemd service:**
   ```bash
   sudo systemctl start tip-scheduler
   sudo systemctl status tip-scheduler
   sudo journalctl -u tip-scheduler -f
   ```
   Watch for 5 minutes to ensure it's stable.

3. **Verify a task runs:**
   - Edit `run_scheduler.py` temporarily to run every 1 minute:
     ```python
     schedule.every(1).minutes.do(run_result_verification)
     ```
   - Restart service: `sudo systemctl restart tip-scheduler`
   - Watch logs: `tail -f /var/log/tip_scheduler.log`
   - You should see verification run within 1 minute
   - Revert to 30 minutes after testing

4. **Check database updates:**
   ```bash
   python manage.py shell
   ```
   ```python
   from apps.tips.models import Tip
   Tip.objects.filter(is_resulted=True).count()
   ```

## Advantages Over Cron

✅ **Better Logging** - Integrated with Python logging
✅ **Error Handling** - Automatic restarts on failure (with systemd)
✅ **Easier Configuration** - Edit Python file instead of crontab
✅ **Platform Independent** - Works on any OS with Python
✅ **No Cron Syntax** - Use readable Python code
✅ **Flexible Scheduling** - Easy to add complex schedules
✅ **Testing** - Can run scheduler manually for testing

## Migration from Cron (if applicable)

If you previously used cron:

```bash
# Remove old cron job
crontab -e
# Delete the verification line

# Verify cron job removed
crontab -l
```

## Support

For issues:
1. Check logs: `tail -f /var/log/tip_scheduler.log`
2. Check service status: `sudo systemctl status tip-scheduler`
3. Run test script: `python test_livescore_verification.py`
4. Run manually: `python run_scheduler.py`

## Additional Resources

- **run_scheduler.py** - Main scheduler script
- **tip-scheduler.service** - Systemd service configuration
- **livescore_scraper.py** - Scraping logic
- **result_verifier.py** - Verification logic
- **LIVESCORE_AUTO_VERIFICATION.md** - Technical documentation
