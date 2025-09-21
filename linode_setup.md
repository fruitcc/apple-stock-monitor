# Linode VPS Deployment Guide

This guide will help you deploy the Apple Stock Monitor on a Linode VPS to run continuously.

## Prerequisites

- A Linode VPS with Ubuntu 22.04 or later
- SSH access to your Linode server
- Python 3.10+ installed on the server

## Step 1: Clone the Repository

SSH into your Linode VPS and clone this repository:

```bash
ssh root@your-linode-ip
cd /opt
git clone https://github.com/YOUR_USERNAME/apple-stock-monitor.git
cd apple-stock-monitor
```

## Step 2: Install Dependencies

```bash
# Update system packages
apt update && apt upgrade -y

# Install Python and pip
apt install python3 python3-pip python3-venv -y

# Install Chrome for Selenium (optional, for full monitor)
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
sh -c 'echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" >> /etc/apt/sources.list.d/google-chrome.list'
apt update
apt install google-chrome-stable -y

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python packages
pip install -r requirements.txt
```

## Step 3: Configure Environment Variables

Create your `.env` file with your email credentials:

```bash
cp .env.example .env
nano .env
```

Edit the file with your Gmail app password:
```
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_app_password_here
EMAIL_TO=fruitcc@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## Step 4: Create Systemd Service

Create a service file to run the monitor continuously:

```bash
nano /etc/systemd/system/apple-monitor.service
```

Add the following content:

```ini
[Unit]
Description=Apple Stock Monitor
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/apple-stock-monitor
Environment="PATH=/opt/apple-stock-monitor/venv/bin:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
ExecStart=/opt/apple-stock-monitor/venv/bin/python /opt/apple-stock-monitor/osaka_stores_monitor.py
Restart=always
RestartSec=10
StandardOutput=append:/var/log/apple-monitor.log
StandardError=append:/var/log/apple-monitor.log

[Install]
WantedBy=multi-user.target
```

## Step 5: Start and Enable the Service

```bash
# Reload systemd
systemctl daemon-reload

# Enable the service to start on boot
systemctl enable apple-monitor

# Start the service
systemctl start apple-monitor

# Check status
systemctl status apple-monitor
```

## Step 6: Monitor Logs

View the monitor logs:

```bash
# View systemd logs
journalctl -u apple-monitor -f

# View application logs
tail -f /var/log/apple-monitor.log
```

## Useful Commands

### Check if monitor is running:
```bash
systemctl status apple-monitor
```

### Stop the monitor:
```bash
systemctl stop apple-monitor
```

### Restart the monitor:
```bash
systemctl restart apple-monitor
```

### Update the code:
```bash
cd /opt/apple-stock-monitor
git pull
systemctl restart apple-monitor
```

### Test email configuration:
```bash
cd /opt/apple-stock-monitor
source venv/bin/activate
python test_email.py
```

## Running with Screen (Alternative Method)

If you prefer using screen instead of systemd:

```bash
# Install screen
apt install screen -y

# Create a new screen session
screen -S apple-monitor

# Run the monitor
cd /opt/apple-stock-monitor
source venv/bin/activate
python osaka_stores_monitor.py

# Detach from screen: Press Ctrl+A, then D

# Reattach to screen
screen -r apple-monitor
```

## Running with Docker (Optional)

Create a Dockerfile:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "osaka_stores_monitor.py"]
```

Build and run:
```bash
docker build -t apple-monitor .
docker run -d --name apple-monitor --restart always apple-monitor
```

## Monitoring Multiple Products

To monitor different products, edit the URL in `osaka_stores_monitor.py`:

```python
url = "https://www.apple.com/jp/shop/buy-iphone/..."  # Change this URL
```

## Security Notes

1. Never commit your `.env` file with real credentials
2. Use strong app passwords for email
3. Consider using a dedicated email account for notifications
4. Regularly update dependencies: `pip install --upgrade -r requirements.txt`

## Troubleshooting

### Monitor not starting:
- Check logs: `journalctl -u apple-monitor -n 50`
- Verify Python path: `which python3`
- Check permissions: `ls -la /opt/apple-stock-monitor`

### Email not sending:
- Test email config: `python test_email.py`
- Verify Gmail app password is correct
- Check firewall allows outbound SMTP (port 587)

### High CPU usage:
- Increase check interval in the code (default is 5 seconds)
- Consider using the cloudscraper-only version instead of Selenium

## Support

For issues or questions, please open an issue on GitHub.