# Chromium Installation Guide

The Apple Stock Monitor uses Chromium/Chrome for web scraping. Here's how to install it on different Linux distributions.

## Ubuntu/Debian

### Ubuntu 22.04+ / Debian 11+
```bash
# The package is called 'chromium' (not chromium-browser)
sudo apt update
sudo apt install chromium

# Or using snap (Ubuntu default)
sudo snap install chromium
```

### Ubuntu 20.04 / Debian 10
```bash
sudo apt update
sudo apt install chromium-browser

# Alternative if above fails
sudo apt install chromium
```

### Ubuntu 18.04
```bash
sudo apt update
sudo apt install chromium-browser
```

## Alternative: Google Chrome

If Chromium isn't available, you can install Google Chrome instead:

```bash
# Download and add Google's signing key
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -

# Add Chrome repository
echo "deb [arch=amd64] http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google-chrome.list

# Update and install Chrome
sudo apt update
sudo apt install google-chrome-stable
```

## CentOS/RHEL/Rocky Linux

```bash
# Install EPEL repository first
sudo yum install epel-release

# Install Chromium
sudo yum install chromium

# Or for newer versions (8+)
sudo dnf install chromium
```

## Fedora

```bash
sudo dnf install chromium
```

## Arch Linux

```bash
sudo pacman -S chromium
```

## Alpine Linux

```bash
sudo apk add chromium chromium-chromedriver
```

## Verify Installation

After installation, verify Chromium is installed:

```bash
# Check if chromium is installed
which chromium || which chromium-browser || which google-chrome

# Check version
chromium --version || chromium-browser --version || google-chrome --version
```

## Headless Server Setup

For VPS/servers without display:

```bash
# Install additional dependencies for headless operation
sudo apt install -y xvfb

# These are usually included but install if missing
sudo apt install -y \
    fonts-liberation \
    libappindicator3-1 \
    libasound2 \
    libatk-bridge2.0-0 \
    libatk1.0-0 \
    libcups2 \
    libdbus-1-3 \
    libdrm2 \
    libgbm1 \
    libgtk-3-0 \
    libnspr4 \
    libnss3 \
    libx11-xcb1 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libxrandr2 \
    libxss1 \
    libxtst6
```

## Docker Alternative

If you can't install Chromium directly, consider using Docker:

```bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Run Chromium in Docker
docker run -d \
  --name chromium \
  -p 9222:9222 \
  --cap-add=SYS_ADMIN \
  zenika/alpine-chrome \
  --no-sandbox \
  --remote-debugging-address=0.0.0.0 \
  --remote-debugging-port=9222
```

## Troubleshooting

### "No sandbox" Error

If you see sandbox-related errors:

```python
# In osaka_stores_monitor.py, add these Chrome options:
chrome_options.add_argument('--no-sandbox')
chrome_options.add_argument('--disable-dev-shm-usage')
```

### Missing Dependencies

If Chromium won't start:

```bash
# Install all dependencies
sudo apt update
sudo apt install -y $(apt-cache depends chromium | grep Depends | sed "s/.*ends:\ //" | tr '\n' ' ')
```

### Permission Issues

```bash
# Fix permissions
sudo usermod -a -G audio,video $USER

# Logout and login again for changes to take effect
```

## Testing Chromium

Create a test script to verify Chromium works:

```python
#!/usr/bin/env python3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

options = Options()
options.add_argument('--headless')
options.add_argument('--no-sandbox')
options.add_argument('--disable-dev-shm-usage')

try:
    driver = webdriver.Chrome(options=options)
    driver.get('https://www.google.com')
    print(f"Success! Page title: {driver.title}")
    driver.quit()
except Exception as e:
    print(f"Error: {e}")
```

Run with:
```bash
python3 test_chromium.py
```

## Using with undetected-chromedriver

The monitor uses `undetected-chromedriver` which automatically downloads the correct Chrome driver. However, it needs Chrome/Chromium installed on the system.

If you have issues:

1. **Clear the cache:**
   ```bash
   rm -rf ~/.cache/selenium
   rm -rf ~/.cache/undetected_chromedriver
   ```

2. **Manually specify Chrome binary:**
   ```python
   # In osaka_stores_monitor.py
   import undetected_chromedriver as uc

   options = uc.ChromeOptions()
   options.binary_location = '/usr/bin/chromium'  # Or your Chrome path
   driver = uc.Chrome(options=options)
   ```

## Cloud Providers

### AWS EC2
- Use Amazon Linux 2: `sudo amazon-linux-extras install chromium`
- Or install Google Chrome using the rpm method

### Google Cloud
- Debian/Ubuntu instances: Use standard apt commands
- Pre-installed in some images

### DigitalOcean
- Ubuntu droplets: Use standard apt commands
- May need to enable swap for small instances

### Linode
- Ubuntu/Debian: Follow distribution-specific instructions above
- Ensure sufficient RAM (minimum 1GB recommended)