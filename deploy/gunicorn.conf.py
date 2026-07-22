"""
Gunicorn configuration for Ligisoo Marketplace
Tuned for GCP e2-micro (0.6 vCPU, 1 GB RAM)

Reference: https://docs.gunicorn.org/en/stable/configure.html
"""

import multiprocessing

# ---------------------------------------------------------------------------
# Server socket
# ---------------------------------------------------------------------------
# Bind to a Unix socket instead of TCP — faster IPC with nginx, no TCP overhead
bind = "unix:/run/gunicorn/ligisoo.sock"
backlog = 64

# ---------------------------------------------------------------------------
# Worker processes
# ---------------------------------------------------------------------------
# Formula: (2 * CPU cores) + 1  →  on e2-micro use 2 to stay within RAM budget.
# Each sync worker on this Django app uses ~80–120 MB.
# 2 workers = ~200 MB peak, leaving headroom for nginx + postgres + redis.
workers = 2
worker_class = "sync"

# Recycle workers after this many requests to prevent memory leaks
max_requests = 500
max_requests_jitter = 50  # add randomness to avoid all workers restarting simultaneously

# ---------------------------------------------------------------------------
# Timeouts
# ---------------------------------------------------------------------------
timeout = 120        # kill and restart a worker that hasn't responded in 120s
keepalive = 5        # how long to wait for the next request on a keep-alive connection
graceful_timeout = 30

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
# systemd captures stdout/stderr via journald — log to stderr so journalctl works
accesslog = "-"   # stdout
errorlog = "-"    # stderr
loglevel = "info"
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)sµs'

# ---------------------------------------------------------------------------
# Process naming
# ---------------------------------------------------------------------------
proc_name = "ligisoo"

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
# Drop privileges after binding if started as root
# (The systemd service starts as the app user directly, so these are no-ops,
#  but they're a good safety net)
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190
