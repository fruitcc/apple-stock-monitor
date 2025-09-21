# Apple Stock Monitor

Automated monitoring system for Apple product availability with email notifications.

## Features

- **Anti-Detection Measures**: Uses undetected-chromedriver and multiple evasion techniques
- **Multiple Detection Methods**: Selenium with fallback to cloudscraper
- **Email Notifications**: Sends alerts when products come in stock
- **Configurable Monitoring**: Customizable check intervals and multiple product support
- **Error Recovery**: Automatic recovery from failures and browser crashes
- **Rate Limiting**: Prevents spam with notification intervals

## Anti-Crawling Countermeasures

The monitor implements several techniques to bypass Apple's anti-bot measures:

1. **Undetected Chrome Driver**: Uses modified Chrome that bypasses detection
2. **Random User Agents**: Rotates user agents to appear as different browsers
3. **Human-like Behavior**: Random delays and scrolling patterns
4. **JavaScript Injection**: Modifies navigator properties to hide automation
5. **Cloudscraper Fallback**: Uses cloudscraper for Cloudflare challenges
6. **Session Management**: Maintains cookies and session data

## Installation

```bash
# Clone or create the directory
cd apple-stock-monitor

# Install dependencies
pip3 install -r requirements.txt

# Install Chrome/Chromium if not already installed
# On macOS:
brew install --cask google-chrome

# On Ubuntu/Debian:
sudo apt-get update
sudo apt-get install chromium-browser
```

## Configuration

### Email Setup (Gmail)

1. Create an App Password for Gmail:
   - Go to Google Account settings
   - Security > 2-Step Verification (must be enabled)
   - App passwords > Generate

2. Edit `.env` file:
```env
EMAIL_FROM=your_email@gmail.com
EMAIL_PASSWORD=your_16_char_app_password
EMAIL_TO=fruitcc@gmail.com
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
```

## Usage

### Basic Usage

```bash
# Monitor default product with 5-second intervals
python3 monitor.py

# Monitor specific products
python3 monitor.py --urls "https://apple.com/product1" "https://apple.com/product2"

# Custom interval (30 seconds)
python3 monitor.py --interval 30

# Show browser window (for debugging)
python3 monitor.py --no-headless
```

### Run in Background

```bash
# Using nohup
nohup python3 monitor.py > monitor.log 2>&1 &

# Using screen
screen -S apple-monitor
python3 monitor.py
# Detach: Ctrl+A, D
# Reattach: screen -r apple-monitor
```

### Systemd Service (Linux)

Create `/etc/systemd/system/apple-monitor.service`:

```ini
[Unit]
Description=Apple Stock Monitor
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/apple-stock-monitor
Environment="PATH=/usr/local/bin:/usr/bin"
ExecStart=/usr/bin/python3 /path/to/apple-stock-monitor/monitor.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable apple-monitor
sudo systemctl start apple-monitor
sudo systemctl status apple-monitor
```

## Monitoring Output

The monitor provides detailed console output:

```
2024-01-01 12:00:00 - Check #1
==================================================
Checking: https://www.apple.com/jp/shop/...
✅ IN STOCK! Method: selenium
   Details: {'indicator': 'Add to cart button found'}
🎉 NEW STOCK DETECTED!
📧 Email notification sent!
```

## Troubleshooting

### Chrome Driver Issues

If you encounter Chrome driver issues:

```bash
# Check Chrome version
google-chrome --version

# The undetected-chromedriver will auto-download matching driver
# Clear cache if needed
rm -rf ~/.cache/selenium
```

### Cloudflare Challenges

The monitor automatically falls back to cloudscraper when Cloudflare is detected. If both methods fail, try:

1. Run with `--no-headless` to see what's happening
2. Increase delays in the code
3. Use a VPN or proxy

### Email Not Sending

1. Verify App Password is correct (not your regular password)
2. Check 2-Step Verification is enabled on Gmail
3. Look for errors in `apple_monitor.log`

## Important Notes

- **Rate Limiting**: Minimum 5 minutes between email notifications for the same product
- **Resource Usage**: Each check uses ~100-200MB RAM with headless Chrome
- **Network**: Ensure stable internet connection for reliability
- **Legal**: Use responsibly and respect Apple's terms of service

## Logs

Logs are written to `apple_monitor.log` and console simultaneously.

## License

For educational purposes only. Use at your own risk.