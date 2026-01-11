import multiprocessing
import os

# Server socket
bind = '0.0.0.0:5000'

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = 'sync'
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = '-'
errorlog = '-'
loglevel = 'info'
access_log_format = '%(h)s %(l)s %(u)s %(t)s "%(r)s" %(s)s %(b)s "%(f)s" "%(a)s"'

# Security
limit_request_line = 4094
limit_request_fields = 100
limit_request_field_size = 8190

# Server mechanics
pidfile = 'gunicorn.pid'
worker_tmp_dir = '/dev/shm'

def on_starting(server):
    # Create upload and output directories if they don't exist
    os.makedirs('uploads', exist_ok=True)
    os.makedirs('outputs', exist_ok=True)
