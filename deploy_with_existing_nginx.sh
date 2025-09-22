#!/bin/bash

# Deployment script for Apple Stock Monitor with existing Nginx setup
# This script assumes you already have Nginx installed and configured

set -e

echo "======================================"
echo "Apple Stock Monitor Deployment"
echo "For VPS with Existing Nginx"
echo "======================================"

# Check if running as root
if [[ $EUID -eq 0 ]]; then
   echo "This script should not be run as root."
   echo "Please run as a regular user with sudo privileges."
   exit 1
fi

# Update system packages
echo "Updating system packages..."
sudo apt-get update

# Install Python and Chrome dependencies only
echo "Installing required dependencies..."
sudo apt-get install -y python3 python3-pip python3-venv

# Install Chromium (package name varies by distribution)
echo "Installing Chromium browser..."
if command -v chromium-browser &> /dev/null; then
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
    read -p "Press Enter to continue after updating .env..."
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
ExecStart=$HOME/apple-stock-monitor/venv/bin/python $HOME/apple-stock-monitor/app.py --production
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

# Configure Nginx
echo ""
echo "======================================"
echo "Nginx Configuration Options"
echo "======================================"
echo ""
echo "Choose how you want to access the Apple Stock Monitor:"
echo "1) Subdomain (e.g., apple.yourdomain.com)"
echo "2) Subdirectory (e.g., yourdomain.com/apple)"
echo "3) Different port (e.g., yourdomain.com:8080)"
echo "4) Skip Nginx configuration (access directly via port 5000)"
echo ""
read -p "Enter your choice (1-4): " nginx_choice

case $nginx_choice in
    1)
        read -p "Enter your subdomain (e.g., apple.yourdomain.com): " subdomain

        # Create Nginx configuration for subdomain
        sudo tee /etc/nginx/sites-available/apple-monitor > /dev/null <<EOF
server {
    listen 80;
    server_name $subdomain;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
EOF

        # Enable the site
        sudo ln -sf /etc/nginx/sites-available/apple-monitor /etc/nginx/sites-enabled/

        echo "Subdomain configuration created for: $subdomain"
        echo "Remember to add DNS A record pointing to your VPS IP"
        ;;

    2)
        read -p "Enter the path prefix (e.g., /apple): " prefix

        # Show instructions for adding to existing server block
        cat > nginx_location_block.txt <<EOF
# Add this location block to your existing server configuration:

location $prefix/ {
    rewrite ^$prefix/(.*) /\$1 break;
    proxy_pass http://127.0.0.1:5001;
    proxy_set_header Host \$host;
    proxy_set_header X-Real-IP \$remote_addr;
    proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto \$scheme;
    proxy_set_header X-Script-Name $prefix;
    proxy_set_header X-Forwarded-Prefix $prefix;
    proxy_buffering off;
}
EOF

        echo ""
        echo "Location block saved to: nginx_location_block.txt"
        echo "Add this to your existing Nginx server configuration"
        echo ""
        read -p "Enter the path to your existing Nginx config file: " config_file

        if [ -f "$config_file" ]; then
            echo ""
            echo "Add the location block from nginx_location_block.txt to: $config_file"
            echo "You can edit it manually or I can show you the contents to add."
            read -p "Show the location block to add? (y/n): " show_block
            if [[ $show_block == "y" ]]; then
                cat nginx_location_block.txt
            fi
        fi
        ;;

    3)
        read -p "Enter the port number (e.g., 8080): " port
        read -p "Enter your domain name: " domain

        # Create Nginx configuration for different port
        sudo tee /etc/nginx/sites-available/apple-monitor-port > /dev/null <<EOF
server {
    listen $port;
    server_name $domain;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_buffering off;
    }
}
EOF

        # Enable the site
        sudo ln -sf /etc/nginx/sites-available/apple-monitor-port /etc/nginx/sites-enabled/

        # Open firewall port
        sudo ufw allow $port/tcp 2>/dev/null || true

        echo "Port configuration created for: $domain:$port"
        ;;

    4)
        echo "Skipping Nginx configuration."
        echo "The web dashboard will be accessible on port 5000"

        # Open firewall port
        sudo ufw allow 5000/tcp 2>/dev/null || true
        ;;
esac

# Test and reload Nginx if configured
if [ "$nginx_choice" != "4" ]; then
    echo "Testing Nginx configuration..."
    if sudo nginx -t; then
        echo "Nginx configuration is valid. Reloading..."
        sudo systemctl reload nginx
    else
        echo "⚠️ Nginx configuration test failed. Please check the configuration."
    fi
fi

# Enable and start services
echo "Enabling and starting services..."
sudo systemctl daemon-reload
sudo systemctl enable apple-monitor.service
sudo systemctl enable apple-web.service
sudo systemctl start apple-monitor.service
sudo systemctl start apple-web.service

# Create log directory and rotation
echo "Setting up log rotation..."
mkdir -p $HOME/apple-stock-monitor/logs

sudo tee /etc/logrotate.d/apple-monitor > /dev/null <<EOF
$HOME/apple-stock-monitor/*.log {
    daily
    missingok
    rotate 7
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

# Display status
echo ""
echo "======================================"
echo "✅ Deployment Complete!"
echo "======================================"
echo ""
echo "Service Status:"
sudo systemctl status apple-monitor.service --no-pager | head -5
echo ""
sudo systemctl status apple-web.service --no-pager | head -5
echo ""

# Show access information based on configuration
echo "Access Information:"
case $nginx_choice in
    1)
        echo "  Web Dashboard: http://$subdomain"
        echo "  (After DNS is configured)"
        ;;
    2)
        echo "  Web Dashboard: http://your-domain$prefix"
        echo "  (After adding location block to Nginx)"
        ;;
    3)
        echo "  Web Dashboard: http://$domain:$port"
        ;;
    4)
        echo "  Web Dashboard: http://$(curl -s ifconfig.me):5000"
        ;;
esac

echo ""
echo "Useful Commands:"
echo "  View monitor logs: tail -f ~/apple-stock-monitor/monitor.log"
echo "  View web logs: sudo journalctl -u apple-web -f"
echo "  Restart monitor: sudo systemctl restart apple-monitor"
echo "  Restart web app: sudo systemctl restart apple-web"
echo "  Check status: sudo systemctl status apple-monitor apple-web"
echo ""
echo "Database location: ~/apple-stock-monitor/stock_history.db"
echo ""

# SSL Certificate reminder
if [ "$nginx_choice" == "1" ]; then
    echo "To enable HTTPS with Let's Encrypt:"
    echo "  sudo certbot --nginx -d $subdomain"
    echo ""
fi