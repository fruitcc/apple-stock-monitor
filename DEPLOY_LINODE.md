# Linode VPS Deployment Guide

This guide will help you deploy the Apple Stock Monitor on a Linode VPS with Ubuntu.

## Prerequisites

- A Linode VPS running Ubuntu 22.04 or later
- SSH access to your VPS
- A domain name (optional, for web access)
- Gmail account with App Password configured

## Quick Deployment

### 1. SSH into your Linode VPS

```bash
ssh root@your-linode-ip
```

### 2. Create a non-root user (if needed)

```bash
adduser monitor
usermod -aG sudo monitor
su - monitor
```

### 3. Download and run the deployment script

```bash
# Download the deployment script
wget https://raw.githubusercontent.com/fruitcc/apple-stock-monitor/main/deploy.sh

# Make it executable
chmod +x deploy.sh

# Run the deployment
./deploy.sh
```

The script will:
- Install all dependencies (Python, Chrome, etc.)
- Clone the repository
- Setup virtual environment
- Configure systemd services
- Setup firewall rules
- Optionally configure Nginx

### 4. Configure your email settings

Edit the `.env` file with your Gmail credentials:

```bash
nano ~/apple-stock-monitor/.env
```

Update these values:
```env
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
EMAIL_TO=recipient@gmail.com
CHECK_INTERVAL=10
```

### 5. Restart services

```bash
sudo systemctl restart apple-monitor apple-web
```

## Manual Deployment Steps

If you prefer manual installation:

### Step 1: System Updates and Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python and required packages
sudo apt install -y python3 python3-pip python3-venv git chromium-browser nginx

# Install Chrome (for undetected-chromedriver)
wget -q -O - https://dl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
sudo sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
sudo apt update
sudo apt install -y google-chrome-stable
```

### Step 2: Clone and Setup Repository

```bash
# Clone repository
cd ~
git clone https://github.com/fruitcc/apple-stock-monitor.git
cd apple-stock-monitor

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python requirements
pip install --upgrade pip
pip install -r requirements.txt
```

### Step 3: Environment Configuration

```bash
# Copy example env file
cp .env.example .env

# Edit with your email settings
nano .env
```

### Step 4: Create Systemd Services

Create monitor service:

```bash
sudo nano /etc/systemd/system/apple-monitor.service
```

```ini
[Unit]
Description=Apple Stock Monitor
After=network.target

[Service]
Type=simple
User=monitor
WorkingDirectory=/home/monitor/apple-stock-monitor
Environment="PATH=/home/monitor/apple-stock-monitor/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/home/monitor/apple-stock-monitor/venv/bin/python /home/monitor/apple-stock-monitor/osaka_stores_monitor.py
Restart=always
RestartSec=10
StandardOutput=append:/home/monitor/apple-stock-monitor/monitor.log
StandardError=append:/home/monitor/apple-stock-monitor/monitor.log

[Install]
WantedBy=multi-user.target
```

Create web service:

```bash
sudo nano /etc/systemd/system/apple-web.service
```

```ini
[Unit]
Description=Apple Stock Monitor Web Dashboard
After=network.target

[Service]
Type=simple
User=monitor
WorkingDirectory=/home/monitor/apple-stock-monitor
Environment="PATH=/home/monitor/apple-stock-monitor/venv/bin:/usr/local/bin:/usr/bin"
ExecStart=/home/monitor/apple-stock-monitor/venv/bin/python /home/monitor/apple-stock-monitor/app_production.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Step 5: Configure Nginx (Recommended)

```bash
sudo nano /etc/nginx/sites-available/apple-monitor
```

```nginx
server {
    listen 80;
    server_name your-domain.com;  # Or use your Linode IP

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/apple-monitor /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Step 6: Setup Firewall

```bash
# Allow SSH, HTTP, and HTTPS
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

### Step 7: Start Services

```bash
# Enable services to start on boot
sudo systemctl enable apple-monitor apple-web nginx

# Start all services
sudo systemctl start apple-monitor apple-web nginx

# Check status
sudo systemctl status apple-monitor apple-web nginx
```

## SSL Certificate (Optional)

For HTTPS, install Certbot:

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d your-domain.com
```

## Monitoring and Maintenance

### View Logs

```bash
# Monitor logs
tail -f ~/apple-stock-monitor/monitor.log

# Flask logs
tail -f ~/apple-stock-monitor/flask.log

# System logs
sudo journalctl -u apple-monitor -f
sudo journalctl -u apple-web -f
```

### Check Database

```bash
cd ~/apple-stock-monitor
sqlite3 stock_history.db

# View recent checks
SELECT * FROM availability_history ORDER BY checked_at DESC LIMIT 10;

# View changes
SELECT * FROM availability_changes ORDER BY changed_at DESC;
```

### Update Code

```bash
cd ~/apple-stock-monitor
git pull
sudo systemctl restart apple-monitor apple-web
```

### Service Management

```bash
# Start services
sudo systemctl start apple-monitor apple-web

# Stop services
sudo systemctl stop apple-monitor apple-web

# Restart services
sudo systemctl restart apple-monitor apple-web

# View status
sudo systemctl status apple-monitor apple-web
```

## Troubleshooting

### Chrome Driver Issues

If you encounter Chrome driver problems:

```bash
# Check Chrome version
google-chrome --version

# Clear cache
rm -rf ~/.cache/selenium

# Reinstall undetected-chromedriver
source ~/apple-stock-monitor/venv/bin/activate
pip install --upgrade undetected-chromedriver
```

### Service Won't Start

Check logs:
```bash
sudo journalctl -u apple-monitor -n 50
sudo journalctl -u apple-web -n 50
```

Common fixes:
```bash
# Fix permissions
sudo chown -R monitor:monitor ~/apple-stock-monitor

# Check Python path
which python3

# Verify virtual environment
source ~/apple-stock-monitor/venv/bin/activate
which python
```

### Web Dashboard Not Accessible

1. Check if Flask is running:
```bash
sudo systemctl status apple-web
curl http://localhost:5000
```

2. Check Nginx:
```bash
sudo nginx -t
sudo systemctl status nginx
```

3. Check firewall:
```bash
sudo ufw status
```

## Performance Tuning

### Reduce Memory Usage

For smaller VPS instances (1GB RAM):

1. Edit monitor to use headless Chrome only
2. Increase check interval in `.env`:
```env
CHECK_INTERVAL=30  # Check every 30 seconds instead of 10
```

3. Limit Chrome memory:
```python
# In osaka_stores_monitor.py, add Chrome options:
chrome_options.add_argument('--memory-pressure-off')
chrome_options.add_argument('--disable-gpu')
chrome_options.add_argument('--disable-dev-shm-usage')
```

### Database Maintenance

Clean old records periodically:
```sql
-- Delete records older than 30 days
DELETE FROM availability_history WHERE checked_at < datetime('now', '-30 days');
VACUUM;
```

## Monitoring Multiple Products

To monitor different products, edit `osaka_stores_monitor.py`:

```python
# Line 285 - Change the URL
url = "https://www.apple.com/jp/shop/buy-iphone/..."
```

Then restart:
```bash
sudo systemctl restart apple-monitor
```

## Support

For issues or questions:
- Check logs first: `tail -f ~/apple-stock-monitor/monitor.log`
- GitHub Issues: https://github.com/fruitcc/apple-stock-monitor/issues

## Security Notes

1. Keep your `.env` file secure
2. Use strong passwords for VPS access
3. Keep system updated: `sudo apt update && sudo apt upgrade`
4. Consider using fail2ban for SSH protection
5. Use HTTPS with SSL certificate for web dashboard