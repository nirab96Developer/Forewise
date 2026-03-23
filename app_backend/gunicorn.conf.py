# gunicorn.conf.py
"""
Gunicorn configuration for Forest Management System
הגדרות Gunicorn למערכת ניהול יערות
"""
import multiprocessing
import os

# Server socket
bind = f"0.0.0.0:{os.getenv('PORT', '8000')}"
backlog = 2048

# Worker processes
workers = int(os.getenv('WORKERS', multiprocessing.cpu_count() * 2 + 1))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers after this many requests, to help prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Logging — stdout/stderr captured by systemd journal
accesslog = "-"
errorlog  = "-"
loglevel  = os.getenv('LOG_LEVEL', 'info').lower()
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = "forest-management-system"

# Server mechanics — daemon/pidfile controlled by CLI flags
pidfile = "/tmp/gunicorn.pid"
user = None
group = None
tmp_upload_dir = None

# SSL (if needed)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"

# Environment variables
raw_env = [
    f"ENVIRONMENT={os.getenv('ENVIRONMENT', 'production')}",
    f"DEBUG={os.getenv('DEBUG', 'False')}",
    f"LOG_LEVEL={os.getenv('LOG_LEVEL', 'INFO')}",
]

# Preload app for better performance (works fine with systemd Type=simple)
preload_app = True

# Worker timeout
worker_tmp_dir = "/dev/shm"

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("🌲 Forest Management System server is ready!")

def worker_int(worker):
    """Called just after a worker exited on SIGINT or SIGQUIT."""
    worker.log.info(f"Worker {worker.pid} received SIGINT or SIGQUIT")

def pre_fork(server, worker):
    """Called just before a worker is forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def post_fork(server, worker):
    """Called just after a worker has been forked."""
    server.log.info(f"Worker spawned (pid: {worker.pid})")

def pre_exec(server):
    """Called just before a new master process is forked."""
    server.log.info("Forked child, re-executing.")

def when_ready(server):
    """Called just after the server is started."""
    server.log.info("🌲 Forest Management System server is ready!")

def worker_abort(worker):
    """Called when a worker received the SIGABRT signal."""
    worker.log.info(f"Worker {worker.pid} received SIGABRT")






