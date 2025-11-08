# Pod/Production Deployment Debugging Guide

## Issue: Service Crashing in Pod

If you see:
```
tip-scheduler.service: Main process exited, code=exited, status=1/FAILURE
tip-scheduler.service: Failed with result 'exit-code'
```

Follow these steps to debug:

## Step 1: Get the Actual Error Message

### Option A: Check journalctl logs
```bash
# SSH into your pod, then:
sudo journalctl -u tip-scheduler -n 100 --no-pager
```

### Option B: Check error log file
```bash
# In your pod:
cat /path/to/marketplace/logs/tip_scheduler_error.log
tail -n 50 /path/to/marketplace/logs/tip_scheduler_error.log
```

### Option C: Run script manually to see error
```bash
# SSH into pod, navigate to project directory
cd /path/to/marketplace

# Activate virtual environment
source venv/bin/activate  # or wherever your venv is

# Run the script manually
python run_scheduler.py
```

This will show you the actual error!

## Step 2: Common Pod Issues & Fixes

### Issue 1: Wrong Paths in Service File

**Symptom:** `FileNotFoundError`, `No such file or directory`

**Fix:** Update `tip-scheduler.service` with correct pod paths

```bash
# In your pod, find the correct paths:
whoami                        # Current user
pwd                           # Current directory when in project root
which python                  # Python path (use this in ExecStart)
```

Then update the service file:
```ini
[Service]
User=your-pod-user           # From 'whoami'
WorkingDirectory=/app        # Or wherever your project is
ExecStart=/usr/local/bin/python /app/run_scheduler.py  # Use actual paths
StandardOutput=append:/app/logs/tip_scheduler.log
StandardError=append:/app/logs/tip_scheduler_error.log
```

### Issue 2: Logs Directory Doesn't Exist

**Symptom:** `Permission denied` or `No such file or directory` for logs

**Fix:**
```bash
# In pod:
mkdir -p logs
chmod 755 logs
```

### Issue 3: Wrong Django Settings

**Symptom:** `ImproperlyConfigured`, database connection errors

**Fix:** Update service file to use production settings:
```ini
Environment="DJANGO_SETTINGS_MODULE=config.settings.production"
```

Or in `run_scheduler.py`, change:
```python
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.production')
```

### Issue 4: Database Not Accessible

**Symptom:** `OperationalError`, `could not connect to server`

**Fix:** Ensure database service is running and accessible
```bash
# Test database connection in pod:
python manage.py check --database default
```

### Issue 5: Missing Dependencies

**Symptom:** `ModuleNotFoundError`, `No module named 'schedule'`

**Fix:**
```bash
# In pod:
pip install -r requirements.txt
```

### Issue 6: Virtual Environment Issues

**Symptom:** Import errors, module not found

**Fix:** Don't use virtual environment in service file, use system Python:
```ini
ExecStart=/usr/bin/python3 /app/run_scheduler.py
```

Or ensure venv is properly set up:
```bash
# In pod:
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue 7: Permission Issues

**Symptom:** `Permission denied`

**Fix:**
```bash
# Make script executable
chmod +x run_scheduler.py

# Fix log permissions
chmod 666 logs/tip_scheduler*.log

# Or run as root (not recommended but works)
# In service file:
User=root
```

## Step 3: Test Manually First

Before using systemd, test the script works in your pod:

```bash
# SSH into pod
cd /path/to/marketplace

# Test the scheduler script directly
python run_scheduler.py
# Should start and show: "Scheduler is running. Press Ctrl+C to stop."
# Press Ctrl+C after a few seconds

# Test result verification
python test_scheduler.py

# Test cleanup
python test_cleanup.py
```

If these work, the issue is in the systemd configuration, not the code.

## Step 4: Simplified Service File for Pods

For containerized environments, use this minimal service file:

```ini
[Unit]
Description=Tip Scheduler
After=network.target

[Service]
Type=simple
WorkingDirectory=/app
ExecStart=/usr/bin/python3 /app/run_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Step 5: Alternative - Don't Use Systemd in Pods

In containerized environments (Docker/Kubernetes), it's often better to run as the main process:

### Option A: Docker Compose
```yaml
services:
  scheduler:
    build: .
    command: python run_scheduler.py
    volumes:
      - ./logs:/app/logs
    depends_on:
      - db
```

### Option B: Kubernetes Deployment
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: tip-scheduler
spec:
  replicas: 1
  template:
    spec:
      containers:
      - name: scheduler
        image: your-image
        command: ["python", "run_scheduler.py"]
```

### Option C: Simple Background Process
```bash
# In pod, run in background:
nohup python run_scheduler.py > logs/scheduler.log 2>&1 &

# Check it's running:
ps aux | grep run_scheduler

# Stop it:
pkill -f run_scheduler.py
```

## Step 6: Get Help from Logs

Once you run the script manually or get the error logs, look for:

1. **Import Errors**
   ```
   ModuleNotFoundError: No module named 'X'
   ```
   → Install missing package: `pip install X`

2. **Database Errors**
   ```
   django.db.utils.OperationalError
   ```
   → Check database connection settings

3. **Permission Errors**
   ```
   PermissionError: [Errno 13]
   ```
   → Fix file/directory permissions

4. **Path Errors**
   ```
   FileNotFoundError: [Errno 2]
   ```
   → Update paths in service file or run_scheduler.py

## Quick Debugging Checklist

Run these commands in your pod:

```bash
# 1. Check Python version
python --version

# 2. Check Django
python -c "import django; print(django.VERSION)"

# 3. Check schedule library
python -c "import schedule; print('OK')"

# 4. Check project imports
cd /path/to/marketplace
python -c "from apps.tips.models import Tip; print('OK')"

# 5. Check database
python manage.py check

# 6. Run migrations if needed
python manage.py migrate

# 7. Test the scheduler
python run_scheduler.py
```

## Still Failing?

Share the actual error message from:
```bash
sudo journalctl -u tip-scheduler -n 50 --no-pager
```

Or:
```bash
python run_scheduler.py  # Run manually and share the error
```

That will show the exact issue!
