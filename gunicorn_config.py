"""
Gunicorn configuration file for SEMrush Data Processor
"""
import multiprocessing
import os

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = int(os.getenv('GUNICORN_WORKERS', '2'))
worker_class = 'gthread'
threads = int(os.getenv('GUNICORN_THREADS', '2'))
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
timeout = 300
keepalive = 5

# Logging
accesslog = '/var/log/semrush-processor/access.log'
errorlog = '/var/log/semrush-processor/error.log'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s" %(D)s'

# Process naming
proc_name = 'semrush-processor'

# Server mechanics
daemon = False
pidfile = '/var/run/semrush-processor.pid'
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (uncomment when you have SSL certificates)
# keyfile = '/etc/ssl/private/your-domain.key'
# certfile = '/etc/ssl/certs/your-domain.crt'

# Server hooks
def on_starting(server):
    """Called just before the master process is initialized"""
    print("Starting SEMrush Data Processor...")

def on_reload(server):
    """Called to recycle workers during a reload"""
    print("Reloading SEMrush Data Processor...")

def when_ready(server):
    """Called just after the server is started"""
    print("SEMrush Data Processor is ready to accept connections")

def worker_int(worker):
    """Called when a worker receives the SIGINT or SIGQUIT signal"""
    print(f"Worker {worker.pid} received shutdown signal")

def worker_abort(worker):
    """Called when a worker receives the SIGABRT signal"""
    print(f"Worker {worker.pid} aborted")
