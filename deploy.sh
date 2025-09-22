#!/bin/bash

# Deployment script for Apple Stock Monitor on Linode VPS
# This script sets up the monitoring system with web dashboard

set -e

echo "======================================"
echo "Apple Stock Monitor Deployment Script"
echo "======================================"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root for security reasons."
   echo "Please run as a regular user with sudo privileges."
   exit 1
fi

# Update system
echo "Updating system packages..."
sudo apt-get update
sudo apt-get upgrade -y

# Install Python and dependencies
echo "Installing Python and system dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv git

# Install Chromium (package name varies by distribution)
echo "Installing Chromium browser..."
if command -v chromium-browser &> /dev/null || command -v chromium &> /dev/null; then
    echo "Chromium already installed"
elif sudo apt-get install -y chromium-browser 2>/dev/null; then
    echo "Installed chromium-browser"
elif sudo apt-get install -y chromium 2>/dev/null; then
    echo "Installed chromium"
else
    # For Ubuntu 20.04+ and Debian, try snap
    echo "Trying snap installation..."
    sudo snap install chromium 2>/dev/null || {
        echo "Warning: Could not install Chromium automatically."
        echo "Please install Chromium manually:"
        echo "  Ubuntu/Debian: sudo apt-get install chromium"
        echo "  Or: sudo snap install chromium"
    }
fi

# Clone or update repository
if [ ! -d "$HOME/apple-stock-monitor" ]; then
    echo "Cloning repository..."
    cd $HOME
    git clone https://github.com/fruitcc/apple-stock-monitor.git
    cd apple-stock-monitor
else
    echo "Updating repository..."
    cd $HOME/apple-stock-monitor
    git pull
fi

# Create virtual environment
echo "Setting up Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
fi

# Activate virtual environment and install requirements
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# Setup environment variables
if [ ! -f ".env" ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Please edit the .env file with your email configuration:"
    echo "    nano .env"
    echo ""
    echo "Press Enter to continue after updating .env..."
    read
fi

# Create systemd service for monitor
echo "Creating systemd service for monitor..."
sudo tee /etc/systemd/system/apple-monitor.service > /dev/null <<EOF
[Unit]
Description=Apple Stock Monitor
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/apple-stock-monitor
Environment="PATH=$HOME/apple-stock-monitor/venv/bin:/usr/local/bin:/usr/bin:/bin"
ExecStart=$HOME/apple-stock-monitor/venv/bin/python $HOME/apple-stock-monitor/osaka_stores_monitor.py
Restart=always
RestartSec=10
StandardOutput=append:$HOME/apple-stock-monitor/monitor.log
StandardError=append:$HOME/apple-stock-monitor/monitor.log

[Install]
WantedBy=multi-user.target
EOF

# Create systemd service for Flask web app
echo "Creating systemd service for web dashboard..."
sudo tee /etc/systemd/system/apple-web.service > /dev/null <<EOF
[Unit]
Description=Apple Stock Monitor Web Dashboard
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$HOME/apple-stock-monitor
Environment="PATH=$HOME/apple-stock-monitor/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="FLASK_APP=app.py"
ExecStart=$HOME/apple-stock-monitor/venv/bin/python $HOME/apple-stock-monitor/app.py --production
Restart=always
RestartSec=10
StandardOutput=append:$HOME/apple-stock-monitor/flask.log
StandardError=append:$HOME/apple-stock-monitor/flask.log

[Install]
WantedBy=multi-user.target
EOF

# Setup nginx (optional, for production)
read -p "Do you want to setup Nginx as a reverse proxy? (y/n): " setup_nginx

if [[ $setup_nginx == "y" ]]; then
    sudo apt-get install -y nginx

    read -p "Enter your domain name (or press Enter to use IP address): " domain_name
    if [ -z "$domain_name" ]; then
        domain_name=$(curl -s ifconfig.me)
    fi

    sudo tee /etc/nginx/sites-available/apple-monitor > /dev/null <<EOF
server {
    listen 80;
    server_name $domain_name;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_read_timeout 90;
        proxy_connect_timeout 90;
    }

    location /api {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}
EOF

    sudo ln -sf /etc/nginx/sites-available/apple-monitor /etc/nginx/sites-enabled/
    sudo nginx -t
    sudo systemctl restart nginx
    sudo systemctl enable nginx

    echo "Nginx configured for domain: $domain_name"
fi

# Setup firewall
echo "Configuring firewall..."
sudo ufw allow 22/tcp  # SSH
sudo ufw allow 80/tcp  # HTTP
sudo ufw allow 443/tcp # HTTPS
if [[ $setup_nginx != "y" ]]; then
    sudo ufw allow 5000/tcp  # Flask (if not using nginx)
fi
sudo ufw --force enable

# Enable and start services
echo "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable apple-monitor.service
sudo systemctl enable apple-web.service
sudo systemctl start apple-monitor.service
sudo systemctl start apple-web.service

# Create log rotation
echo "Setting up log rotation..."
sudo tee /etc/logrotate.d/apple-monitor > /dev/null <<EOF
$HOME/apple-stock-monitor/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 $USER $USER
    sharedscripts
    postrotate
        systemctl reload apple-monitor.service 2>/dev/null || true
        systemctl reload apple-web.service 2>/dev/null || true
    endscript
}
EOF

# Display status and information
echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "Services Status:"
sudo systemctl status apple-monitor.service --no-pager | head -10
echo ""
sudo systemctl status apple-web.service --no-pager | head -10
echo ""
echo "Access Information:"
if [[ $setup_nginx == "y" ]]; then
    echo "Web Dashboard: http://$domain_name"
else
    echo "Web Dashboard: http://$(curl -s ifconfig.me):5000"
fi
echo ""
echo "Useful Commands:"
echo "  View monitor logs: tail -f ~/apple-stock-monitor/monitor.log"
echo "  View web logs: tail -f ~/apple-stock-monitor/flask.log"
echo "  Restart monitor: sudo systemctl restart apple-monitor.service"
echo "  Restart web app: sudo systemctl restart apple-web.service"
echo "  Check service status: sudo systemctl status apple-monitor apple-web"
echo "  View database: sqlite3 ~/apple-stock-monitor/stock_history.db"
echo ""
echo "To stop services:"
echo "  sudo systemctl stop apple-monitor apple-web"
echo ""
echo "To update the code:"
echo "  cd ~/apple-stock-monitor && git pull && sudo systemctl restart apple-monitor apple-web"
echo "