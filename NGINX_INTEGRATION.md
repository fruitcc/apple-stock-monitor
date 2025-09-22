# Nginx Integration Guide

This guide helps you integrate Apple Stock Monitor with your existing Nginx setup on VPS.

## Quick Setup

Use the deployment script for existing Nginx setups:

```bash
wget https://raw.githubusercontent.com/fruitcc/apple-stock-monitor/main/deploy_with_existing_nginx.sh
chmod +x deploy_with_existing_nginx.sh
./deploy_with_existing_nginx.sh
```

The script will guide you through different configuration options.

## Manual Configuration Options

### Option 1: Subdomain (Recommended)

Create a new subdomain like `apple.yourdomain.com`:

1. **Add DNS A Record:**
   - Point `apple.yourdomain.com` to your VPS IP

2. **Create Nginx Configuration:**
   ```bash
   sudo nano /etc/nginx/sites-available/apple-monitor
   ```

   ```nginx
   server {
       listen 80;
       server_name apple.yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_buffering off;
       }
   }
   ```

3. **Enable and Test:**
   ```bash
   sudo ln -s /etc/nginx/sites-available/apple-monitor /etc/nginx/sites-enabled/
   sudo nginx -t
   sudo systemctl reload nginx
   ```

4. **Add SSL (Optional):**
   ```bash
   sudo certbot --nginx -d apple.yourdomain.com
   ```

### Option 2: Subdirectory

Add to your existing domain as `yourdomain.com/apple`:

1. **Edit Your Existing Server Block:**
   ```bash
   sudo nano /etc/nginx/sites-available/your-existing-site
   ```

2. **Add Location Block:**
   ```nginx
   server {
       listen 80;
       server_name yourdomain.com;

       # Your existing configuration...

       # Add this for Apple Monitor
       location /apple/ {
           rewrite ^/apple/(.*) /$1 break;
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_set_header X-Script-Name /apple;
           proxy_set_header X-Forwarded-Prefix /apple;
           proxy_buffering off;
       }
   }
   ```

3. **Test and Reload:**
   ```bash
   sudo nginx -t
   sudo systemctl reload nginx
   ```

### Option 3: Different Port

Use a different port like `yourdomain.com:8080`:

1. **Create Configuration:**
   ```nginx
   server {
       listen 8080;
       server_name yourdomain.com;

       location / {
           proxy_pass http://127.0.0.1:5000;
           proxy_set_header Host $host;
           proxy_set_header X-Real-IP $remote_addr;
           proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
           proxy_set_header X-Forwarded-Proto $scheme;
           proxy_buffering off;
       }
   }
   ```

2. **Open Firewall Port:**
   ```bash
   sudo ufw allow 8080/tcp
   ```

## Advanced Configuration

### Load Balancing (Multiple Flask Instances)

For high availability, run multiple Flask instances:

```nginx
upstream apple_backend {
    server 127.0.0.1:5000;
    server 127.0.0.1:5001;
    server 127.0.0.1:5002;
}

server {
    listen 80;
    server_name apple.yourdomain.com;

    location / {
        proxy_pass http://apple_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

### Caching Static Assets

Add caching for better performance:

```nginx
location /static/ {
    alias /home/your-user/apple-stock-monitor/static/;
    expires 1d;
    add_header Cache-Control "public, immutable";
}

location / {
    proxy_pass http://127.0.0.1:5000;
    # ... other proxy settings
}
```

### Rate Limiting

Protect your application from abuse:

```nginx
# Add to http block in /etc/nginx/nginx.conf
limit_req_zone $binary_remote_addr zone=apple_limit:10m rate=30r/m;

# In your server block
location / {
    limit_req zone=apple_limit burst=5 nodelay;
    proxy_pass http://127.0.0.1:5000;
    # ... other proxy settings
}
```

## Security Headers

Add security headers for production:

```nginx
server {
    listen 80;
    server_name apple.yourdomain.com;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "no-referrer-when-downgrade" always;
    add_header Content-Security-Policy "default-src 'self' http: https: data: blob: 'unsafe-inline'" always;

    location / {
        proxy_pass http://127.0.0.1:5000;
        # ... proxy settings
    }
}
```

## Systemd Services

The deployment creates two services:

### Monitor Service
- **Name:** `apple-monitor.service`
- **Function:** Runs the stock checking monitor
- **Logs:** `~/apple-stock-monitor/monitor.log`

### Web Service
- **Name:** `apple-web.service`
- **Function:** Runs Flask web dashboard
- **Port:** 5000 (internal only, accessed via Nginx)

### Service Commands

```bash
# Start services
sudo systemctl start apple-monitor apple-web

# Stop services
sudo systemctl stop apple-monitor apple-web

# Restart services
sudo systemctl restart apple-monitor apple-web

# View status
sudo systemctl status apple-monitor apple-web

# View logs
sudo journalctl -u apple-monitor -f
sudo journalctl -u apple-web -f

# Enable auto-start on boot
sudo systemctl enable apple-monitor apple-web
```

## Troubleshooting

### 502 Bad Gateway

Flask app not running:
```bash
sudo systemctl status apple-web
sudo systemctl restart apple-web
```

### 404 Not Found (Subdirectory)

Check if rewrite rule is correct:
```nginx
location /apple/ {
    rewrite ^/apple/(.*) /$1 break;  # This line is important
    proxy_pass http://127.0.0.1:5000;
}
```

### Permission Denied

Fix ownership:
```bash
sudo chown -R $USER:$USER ~/apple-stock-monitor
```

### Check Flask is Running

```bash
curl http://localhost:5000
```

### Check Nginx Error Log

```bash
sudo tail -f /var/log/nginx/error.log
```

## Integration with Other Apps

If you're running multiple applications:

### Organize by Subdomain
```
app1.domain.com → App 1
app2.domain.com → App 2
apple.domain.com → Apple Monitor
```

### Organize by Path
```
domain.com/ → Main site
domain.com/app1 → App 1
domain.com/app2 → App 2
domain.com/apple → Apple Monitor
```

### Organize by Port
```
domain.com → Main site (port 80)
domain.com:8080 → App 1
domain.com:8081 → App 2
domain.com:8082 → Apple Monitor
```

## Best Practices

1. **Use Subdomains** for cleaner separation
2. **Enable SSL** with Let's Encrypt
3. **Set Up Monitoring** with tools like Uptime Kuma
4. **Regular Backups** of the SQLite database
5. **Log Rotation** to prevent disk space issues
6. **Resource Limits** in systemd services if needed

## Example Full Configuration

Complete example with SSL and all features:

```nginx
server {
    listen 80;
    server_name apple.yourdomain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name apple.yourdomain.com;

    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/apple.yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/apple.yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header X-Content-Type-Options "nosniff" always;

    # Logging
    access_log /var/log/nginx/apple-access.log;
    error_log /var/log/nginx/apple-error.log;

    # Proxy to Flask
    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto https;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;

        # Buffering
        proxy_buffering off;

        # WebSocket support (for future features)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```