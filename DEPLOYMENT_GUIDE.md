# SEMrush Data Processor - Production Deployment Guide

## 🚀 Quick Start

### From Your Mac Terminal

```bash
# 1. Upload your code to the VPS
scp -r /path/to/your/project/* root@104.168.107.216:/var/www/semrush-processor/

# 2. Upload deployment files
scp deploy.sh root@104.168.107.216:/var/www/semrush-processor/
scp semrush-processor.service root@104.168.107.216:/var/www/semrush-processor/
scp gunicorn_config.py root@104.168.107.216:/var/www/semrush-processor/
scp nginx-semrush-processor.conf root@104.168.107.216:/var/www/semrush-processor/
scp app_production.py root@104.168.107.216:/var/www/semrush-processor/app.py

# 3. SSH into your VPS
ssh root@104.168.107.216

# 4. Run deployment script
cd /var/www/semrush-processor
chmod +x deploy.sh
sudo ./deploy.sh
```

## 📦 Manual Deployment Steps

If you prefer to deploy manually or the script fails:

### 1. Connect and Prepare System

```bash
ssh root@104.168.107.216

# Update system
apt update && apt upgrade -y

# Install dependencies
apt install -y python3 python3-pip git curl build-essential nginx

# Install UV
curl -LsSf https://astral.sh/uv/install.sh | sh
export PATH="$HOME/.cargo/bin:$PATH"
```

### 2. Upload Application Files

```bash
# Create directory
mkdir -p /var/www/semrush-processor
cd /var/www/semrush-processor

# Option A: SCP from your Mac (run from Mac terminal)
scp -r /path/to/local/project/* root@104.168.107.216:/var/www/semrush-processor/

# Option B: Git (recommended for version control)
git clone <your-repo-url> .
```

### 3. Install Dependencies

```bash
cd /var/www/semrush-processor
uv sync
mkdir -p /var/log/semrush-processor
mkdir -p /tmp/semrush_uploads
```

### 4. Configure Environment

```bash
# Generate a secure secret key
python3 -c 'import secrets; print(secrets.token_hex(32))'

# Create environment file
cat > .env << 'EOF'
SECRET_KEY=<paste-generated-key-here>
MAX_FILE_SIZE_MB=100
MAX_WORKERS=2
UPLOAD_FOLDER=/tmp/semrush_uploads
EOF
```

### 5. Set Up Systemd Service

```bash
# Copy service file
cp semrush-processor.service /etc/systemd/system/

# Update SECRET_KEY in service file
nano /etc/systemd/system/semrush-processor.service
# Replace CHANGE_THIS_TO_RANDOM_STRING with your generated secret key

# Enable and start service
systemctl daemon-reload
systemctl enable semrush-processor
systemctl start semrush-processor

# Check status
systemctl status semrush-processor
```

### 6. Configure Nginx (Optional but Recommended)

```bash
# Copy nginx config
cp nginx-semrush-processor.conf /etc/nginx/sites-available/semrush-processor

# Enable site
ln -s /etc/nginx/sites-available/semrush-processor /etc/nginx/sites-enabled/

# Test configuration
nginx -t

# Restart nginx
systemctl restart nginx
```

## 🌐 Accessing Your Application

### Without Domain (Current State)

1. **Direct Access (Port 8000):**
   ```
   http://104.168.107.216:8000
   ```

2. **Via Nginx (Port 80):**
   ```
   http://104.168.107.216
   ```

### With Domain (Future Setup)

1. **Point your domain DNS:**
   - Create an A record: `yourdomain.com` → `104.168.107.216`
   - Create an A record: `www.yourdomain.com` → `104.168.107.216`

2. **Update Nginx configuration:**
   ```bash
   nano /etc/nginx/sites-available/semrush-processor
   # Change: server_name 104.168.107.216;
   # To: server_name yourdomain.com www.yourdomain.com;
   
   systemctl restart nginx
   ```

3. **Set up SSL with Let's Encrypt:**
   ```bash
   apt install certbot python3-certbot-nginx
   certbot --nginx -d yourdomain.com -d www.yourdomain.com
   ```

## 🔒 Security Considerations

### 1. Firewall Setup

```bash
# Install UFW
apt install ufw

# Allow SSH (IMPORTANT: Do this first!)
ufw allow 22/tcp

# Allow HTTP and HTTPS
ufw allow 80/tcp
ufw allow 443/tcp

# Allow Gunicorn (if not using Nginx)
ufw allow 8000/tcp

# Enable firewall
ufw enable
```

### 2. User Isolation & Session Management

The updated `app_production.py` includes:
- **Session-based user isolation**: Each user gets a unique session ID
- **Separate upload directories**: Files are isolated per session
- **Automatic cleanup**: Old files are removed after 24 hours
- **Secure downloads**: Users can only download their own files

### 3. Change Default Credentials

```bash
# Create a non-root user
adduser deploy
usermod -aG sudo deploy

# Update deployment to use non-root user
# Edit /etc/systemd/system/semrush-processor.service
# Change: User=root
# To: User=deploy
```

## 🧪 Memory Management & Leak Prevention

### Built-in Protections

The application includes several memory management features:

1. **Worker Process Limits:**
   - Gunicorn restarts workers after 1000 requests
   - Prevents memory accumulation in long-running processes

2. **Memory-Optimized Data Processing:**
   - Pandas datatype optimization
   - Explicit garbage collection
   - File processing in chunks

3. **Resource Limits:**
   ```python
   # In gunicorn_config.py:
   max_requests = 1000  # Restart worker after X requests
   max_requests_jitter = 50  # Add randomness to prevent all workers restarting at once
   timeout = 300  # Kill unresponsive workers
   ```

4. **Automatic File Cleanup:**
   - Uploaded files deleted immediately after processing
   - Temp directories cleaned after 24 hours
   - Session directories removed when empty

### Monitoring Memory Usage

```bash
# Check overall memory
free -h

# Monitor Gunicorn processes
ps aux | grep gunicorn

# Check memory per worker
top -p $(pgrep -d',' -f gunicorn)

# View detailed memory stats
systemctl status semrush-processor
```

### Memory Leak Detection

```bash
# Install memory profiling tools
pip install memory-profiler

# Add to your code (for testing):
from memory_profiler import profile

@profile
def process_csv_files(...):
    # existing code
```

## 🔧 UV in Production - Best Practices

### Why UV is Safe for Production

1. **Fast & Reliable:** UV is built in Rust, faster than pip
2. **Lock Files:** Ensures consistent dependencies via `uv.lock`
3. **Virtual Environments:** Automatically managed
4. **Reproducible Builds:** Same versions every time

### Production Considerations

```bash
# Lock dependencies for production
uv lock

# Deploy locked dependencies
uv sync --frozen

# Update dependencies (on dev, then deploy)
uv sync --upgrade
uv lock
# Commit uv.lock to git
```

### Environment Variables

```bash
# Set in systemd service or .env file
UV_SYSTEM_PYTHON=1  # Use system Python
UV_NO_CACHE=1  # Don't cache in production
```

## 📊 Monitoring & Logging

### View Logs

```bash
# Application logs
tail -f /var/log/semrush-processor/error.log
tail -f /var/log/semrush-processor/access.log

# System logs
journalctl -u semrush-processor -f

# Nginx logs
tail -f /var/log/nginx/semrush-processor-error.log
```

### Log Rotation

```bash
# Create logrotate config
cat > /etc/logrotate.d/semrush-processor << 'EOF'
/var/log/semrush-processor/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 root root
    sharedscripts
    postrotate
        systemctl reload semrush-processor > /dev/null 2>&1 || true
    endscript
}
EOF
```

## 🚨 Troubleshooting

### Service Won't Start

```bash
# Check service status
systemctl status semrush-processor

# View detailed logs
journalctl -u semrush-processor -n 100

# Check if port is in use
netstat -tulpn | grep 8000

# Test gunicorn directly
cd /var/www/semrush-processor
uv run gunicorn -w 1 -b 0.0.0.0:8000 app:app
```

### High Memory Usage

```bash
# Reduce workers in gunicorn_config.py
workers = 1  # Start with fewer workers

# Reduce max_requests
max_requests = 500  # Restart workers more frequently

# Restart service
systemctl restart semrush-processor
```

### Files Not Processing

```bash
# Check permissions
ls -la /tmp/semrush_uploads
chown -R deploy:deploy /tmp/semrush_uploads

# Check disk space
df -h

# Clear old temp files
find /tmp -name "semrush_*" -mtime +1 -delete
```

## 🔄 Updating the Application

```bash
# Pull latest code
cd /var/www/semrush-processor
git pull

# Update dependencies
uv sync

# Restart service
systemctl restart semrush-processor

# Check if running
systemctl status semrush-processor
```

## 📈 Performance Tuning

### For 2.5GB VPS

```python
# Recommended gunicorn_config.py settings:
workers = 2  # (2 * CPU cores) + 1, but limited by RAM
threads = 2  # Per worker
worker_class = 'gthread'  # Threaded workers use less memory than sync
max_requests = 1000
timeout = 300  # For large file processing
```

### Optimize for Your Traffic

- **Low traffic (<10 concurrent users):** 2 workers, 2 threads
- **Medium traffic (10-50 users):** 3 workers, 2 threads
- **High traffic (50+ users):** Consider upgrading VPS

## 🎯 Next Steps

1. ✅ Deploy application using provided scripts
2. ✅ Test via IP address: `http://104.168.107.216:8000`
3. ⬜ Point domain to your VPS
4. ⬜ Set up SSL with Let's Encrypt
5. ⬜ Configure monitoring (optional: Sentry, New Relic)
6. ⬜ Set up automated backups
7. ⬜ Create non-root user for security

## 📞 Support

If you encounter issues:
1. Check logs: `journalctl -u semrush-processor -n 100`
2. Test connectivity: `curl http://localhost:8000`
3. Verify dependencies: `uv pip list`
4. Check resources: `free -h && df -h`
