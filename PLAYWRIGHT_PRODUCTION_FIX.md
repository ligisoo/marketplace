# Playwright Browser Installation - Production Fix

## 🚨 Current Issue

```
Failed to process SportPesa link: Executable doesn't exist at /home/ubuntu/.cache/ms-playwright/chromium-1105/chrome-linux/chrome
```

The scheduler is failing because Playwright browsers aren't installed in production.

## ✅ Immediate Fix (Run in Production Pod)

```bash
# SSH into your production pod/server
cd /path/to/your/marketplace

# Install Playwright browsers
playwright install chromium

# Or install all browsers (chromium, firefox, webkit)
playwright install
```

This downloads ~100MB for Chromium. Takes 1-2 minutes.

### Verify Installation

```bash
# Test that it works:
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); print('OK'); browser.close(); p.stop()"
```

Should print `OK` without errors.

## 🔧 If You Get Permission Errors

```bash
# Install system dependencies (may need sudo)
playwright install-deps chromium

# Then install browsers
playwright install chromium
```

## 🐳 Docker/Container Environments

If you're using Docker, add this to your `Dockerfile`:

```dockerfile
# Install Playwright browsers during build
RUN pip install playwright==1.42.0
RUN playwright install chromium
RUN playwright install-deps chromium

# Or use Playwright's official image as base
FROM mcr.microsoft.com/playwright/python:v1.42.0-focal
```

### Docker Compose

```yaml
services:
  web:
    build: .
    volumes:
      - playwright-cache:/root/.cache/ms-playwright
    environment:
      - PLAYWRIGHT_BROWSERS_PATH=/root/.cache/ms-playwright

volumes:
  playwright-cache:
```

## 📦 Automated Installation Script

Create `install_playwright.sh`:

```bash
#!/bin/bash
set -e

echo "Installing Playwright browsers..."

# Install Playwright Python package
pip install playwright==1.42.0

# Install system dependencies
playwright install-deps chromium || echo "Note: install-deps may require sudo"

# Install Chromium browser
playwright install chromium

echo "✓ Playwright browsers installed successfully"

# Verify
python -c "from playwright.sync_api import sync_playwright; p = sync_playwright().start(); browser = p.chromium.launch(); browser.close(); p.stop(); print('✓ Chromium working')"
```

Make it executable and run:
```bash
chmod +x install_playwright.sh
./install_playwright.sh
```

## 🔄 Add to Deployment Process

### If Using systemd service

Add pre-start check to service file:

```ini
[Service]
# Check browsers are installed before starting
ExecStartPre=/usr/bin/python3 -c "from playwright.sync_api import sync_playwright; sync_playwright().start().stop()"
ExecStart=/usr/bin/python3 /app/run_scheduler.py
```

### If Using Supervisor

```ini
[program:tip-scheduler]
command=/usr/bin/python3 /app/run_scheduler.py
directory=/app
autostart=true
autorestart=true
stderr_logfile=/app/logs/scheduler_err.log
stdout_logfile=/app/logs/scheduler_out.log
```

### If Using CI/CD (GitHub Actions, GitLab CI, etc.)

Add to your deployment script:

```yaml
# .github/workflows/deploy.yml
- name: Install Playwright Browsers
  run: |
    pip install playwright==1.42.0
    playwright install chromium
    playwright install-deps chromium
```

## ⚡ Lightweight Alternative - Headless Chrome Only

If storage is limited, install only Chromium (not all browsers):

```bash
# Install only Chromium (~100MB instead of ~300MB for all browsers)
playwright install chromium --with-deps
```

## 🛡️ Graceful Error Handling

To prevent the scheduler from crashing if browsers aren't installed, I'll update the code to handle this gracefully.

## 📊 Storage Requirements

- **Chromium only**: ~100-150 MB
- **All browsers**: ~300-400 MB
- **With dependencies**: +100-200 MB

Make sure your pod/container has enough disk space.

## 🧪 Test After Installation

```bash
# Test the scraper
python -c "
from apps.tips.services import LivescoreScraper
scraper = LivescoreScraper()
matches = scraper.scrape_live_scores_sync()
print(f'Found {len(matches)} matches')
"

# Test SportPesa scraper
python manage.py shell
>>> from apps.tips.ocr import BetslipOCR
>>> ocr = BetslipOCR(provider='sportpesa')
>>> # Test with a real link
```

## 🚀 Production Deployment Checklist

- [ ] SSH into production pod
- [ ] `cd /path/to/marketplace`
- [ ] `playwright install chromium`
- [ ] Test: `python -c "from playwright.sync_api import sync_playwright; ..."`
- [ ] Restart scheduler: `sudo systemctl restart tip-scheduler`
- [ ] Monitor logs: `tail -f logs/tip_scheduler.log`
- [ ] Verify no more Playwright errors

## 🔍 Troubleshooting

### Issue: "No such file or directory: 'playwright'"

```bash
# Playwright CLI not in PATH
python -m playwright install chromium
```

### Issue: "Missing system dependencies"

```bash
# Install OS-level dependencies
sudo playwright install-deps chromium

# Or manually install (Ubuntu/Debian):
sudo apt-get update
sudo apt-get install -y \
    libnss3 \
    libnspr4 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libasound2
```

### Issue: "Browser installation failed"

```bash
# Clean cache and retry
rm -rf ~/.cache/ms-playwright
playwright install chromium
```

### Issue: Running in Docker without root

```bash
# Set Playwright to use non-root user
export PLAYWRIGHT_BROWSERS_PATH=/home/user/.cache/ms-playwright
playwright install chromium
```

## 📝 Next Steps

1. **Immediate**: Run `playwright install chromium` in production
2. **Short-term**: Add to deployment scripts
3. **Long-term**: Build into Docker image or use Playwright base image

After installation, your scheduler should work without errors!
