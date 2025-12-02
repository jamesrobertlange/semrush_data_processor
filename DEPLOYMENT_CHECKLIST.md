# 🚀 Quick Deployment Checklist

## Pre-Deployment (On Your Mac)

- [ ] Download all deployment files from Claude
- [ ] Have your VPS credentials ready (root@104.168.107.216)
- [ ] Ensure you have your project files locally

## Deployment (Run on VPS)

### Option 1: Automated Deployment (Recommended)

```bash
# From your Mac
scp -r /path/to/your/project/* root@104.168.107.216:/var/www/semrush-processor/
scp deploy.sh semrush-processor.service gunicorn_config.py nginx-semrush-processor.conf app_production.py root@104.168.107.216:/var/www/semrush-processor/

# SSH into VPS
ssh root@104.168.107.216

# Run deployment
cd /var/www/semrush-processor
chmod +x deploy.sh
sudo ./deploy.sh
```

- [ ] Upload project files
- [ ] Upload deployment files  
- [ ] Run deploy.sh script
- [ ] Test access at http://104.168.107.216:8000

### Option 2: Manual Deployment

- [ ] SSH into VPS: `ssh root@104.168.107.216`
- [ ] Install system dependencies: `apt update && apt install -y python3 curl nginx`
- [ ] Install UV: `curl -LsSf https://astral.sh/uv/install.sh | sh`
- [ ] Create app directory: `mkdir -p /var/www/semrush-processor`
- [ ] Upload your files
- [ ] Install dependencies: `uv sync`
- [ ] Generate secret key
- [ ] Configure systemd service
- [ ] Start service: `systemctl start semrush-processor`
- [ ] Test application

## Post-Deployment Verification

- [ ] Check service status: `systemctl status semrush-processor`
- [ ] Test upload functionality via browser
- [ ] Check logs: `tail -f /var/log/semrush-processor/error.log`
- [ ] Verify memory usage: `free -h`
- [ ] Process test CSV file

## Security Hardening

- [ ] Set up firewall: `ufw enable`
- [ ] Change SSH port (optional)
- [ ] Create non-root user
- [ ] Set up SSH keys
- [ ] Configure fail2ban (optional)

## Optional Enhancements

- [ ] Point domain to VPS
- [ ] Set up SSL with Let's Encrypt
- [ ] Configure monitoring
- [ ] Set up automated backups
- [ ] Configure log rotation

## Accessing Your App

### Current Access (No Domain):
- Direct: http://104.168.107.216:8000
- Via Nginx: http://104.168.107.216

### With Domain (After DNS Setup):
- http://yourdomain.com
- https://yourdomain.com (after SSL)

## Common Commands

```bash
# Check service status
systemctl status semrush-processor

# View logs
journalctl -u semrush-processor -f
tail -f /var/log/semrush-processor/error.log

# Restart service
systemctl restart semrush-processor

# Check memory usage
free -h
ps aux | grep gunicorn

# Update application
cd /var/www/semrush-processor
git pull
uv sync
systemctl restart semrush-processor
```

## Troubleshooting

If something goes wrong:

1. **Service won't start:**
   ```bash
   journalctl -u semrush-processor -n 50
   ```

2. **Can't access via browser:**
   ```bash
   # Check if port is listening
   netstat -tulpn | grep 8000
   
   # Check firewall
   ufw status
   ```

3. **High memory usage:**
   ```bash
   # Reduce workers in /etc/systemd/system/semrush-processor.service
   # Change: --workers 2
   # To: --workers 1
   systemctl daemon-reload
   systemctl restart semrush-processor
   ```

## Support Files Included

- `app_production.py` - Enhanced Flask app with security features
- `deploy.sh` - Automated deployment script
- `semrush-processor.service` - Systemd service file
- `gunicorn_config.py` - Gunicorn production configuration
- `nginx-semrush-processor.conf` - Nginx reverse proxy config
- `production_config.py` - Production settings
- `DEPLOYMENT_GUIDE.md` - Comprehensive deployment guide

---

**Questions?** Refer to DEPLOYMENT_GUIDE.md for detailed instructions.
