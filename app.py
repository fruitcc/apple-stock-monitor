#!/usr/bin/env python3

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import sqlite3
import pytz
import logging
from database import StockDatabase
from werkzeug.middleware.proxy_fix import ProxyFix
from multi_email_notifier import MultiEmailNotifier
import os

app = Flask(__name__)
# Support for reverse proxy with subdirectory
app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1, x_prefix=1)
db = StockDatabase()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/current-status')
def get_current_status():
    """Get current availability status for all products and stores"""
    status = db.get_current_status()
    response = jsonify(status)
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/availability-timeline')
def get_availability_timeline():
    """Get availability timeline with optional filters"""
    product_id = request.args.get('product_id', type=int)
    store_id = request.args.get('store_id', type=int)
    hours = request.args.get('hours', 24, type=int)

    timeline = db.get_availability_timeline(product_id, store_id, hours)
    return jsonify(timeline)

@app.route('/api/availability-changes')
def get_availability_changes():
    """Get status changes (when items became available/unavailable)"""
    product_id = request.args.get('product_id', type=int)
    store_id = request.args.get('store_id', type=int)
    days = request.args.get('days', 7, type=int)

    changes = db.get_availability_changes(product_id, store_id, days)
    return jsonify(changes)

@app.route('/api/availability-stats/<int:product_id>/<int:store_id>')
def get_availability_stats(product_id, store_id):
    """Get availability statistics for a product/store combination"""
    days = request.args.get('days', 7, type=int)
    stats = db.get_availability_stats(product_id, store_id, days)
    return jsonify(stats)

@app.route('/api/products')
def get_products():
    """Get all tracked products"""
    products = db.get_all_products()
    return jsonify(products)

@app.route('/api/stores')
def get_stores():
    """Get all tracked stores"""
    stores = db.get_all_stores()
    return jsonify(stores)

@app.route('/api/send-test-email', methods=['POST'])
def send_test_email():
    """Send a test email notification"""
    logger.info("=" * 60)
    logger.info("TEST EMAIL REQUEST RECEIVED")
    logger.info(f"Request from: {request.remote_addr}")
    logger.info(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info("=" * 60)

    try:
        # Initialize email notifier
        logger.info("Initializing email notifier...")
        notifier = MultiEmailNotifier()

        # Test data
        store_name = "Test Store"
        product_name = "iPhone 17 Pro Max 256GB (Test)"
        product_url = "https://www.apple.com/jp/shop/buy-iphone/iphone-17-pro"
        status = "Test notification - System is working correctly!"

        logger.info("Sending test notification...")
        # Send the test notification
        result = notifier.send_pickup_alert(store_name, product_name, product_url, status)

        if result:
            logger.info("✅ Test email API: Success")
            return jsonify({
                'success': True,
                'message': f'Test email sent to {os.getenv("EMAIL_TO")}'
            })
        else:
            logger.error("❌ Test email API: Failed to send")
            return jsonify({
                'success': False,
                'error': 'Failed to send test email'
            })

    except Exception as e:
        logger.error(f"❌ Test email API: Exception - {e}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        })

def convert_to_jst(datetime_str):
    """Convert UTC datetime string to JST"""
    if not datetime_str:
        return None

    # Parse the datetime (assuming it's in UTC from SQLite)
    dt = datetime.fromisoformat(datetime_str.replace(' ', 'T'))

    # If datetime is naive, assume it's UTC
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    # Convert to JST
    jst = pytz.timezone('Asia/Tokyo')
    dt_jst = dt.astimezone(jst)

    return dt_jst

@app.template_filter('format_datetime')
def format_datetime(value):
    """Format datetime for display in JST"""
    if value:
        dt_jst = convert_to_jst(value)
        if dt_jst:
            return dt_jst.strftime('%Y-%m-%d %H:%M:%S JST')
    return ''

@app.template_filter('time_ago')
def time_ago(value):
    """Convert datetime to 'time ago' format"""
    if not value:
        return 'never'

    dt_jst = convert_to_jst(value)
    if not dt_jst:
        return 'unknown'

    # Get current time in JST
    jst = pytz.timezone('Asia/Tokyo')
    now = datetime.now(jst)
    diff = now - dt_jst

    seconds = diff.total_seconds()

    if seconds < 60:
        return f"{int(seconds)} seconds ago"
    elif seconds < 3600:
        return f"{int(seconds / 60)} minutes ago"
    elif seconds < 86400:
        return f"{int(seconds / 3600)} hours ago"
    else:
        return f"{int(seconds / 86400)} days ago"

if __name__ == '__main__':
    # Check if running in production
    import sys
    if '--production' in sys.argv:
        app.run(host='0.0.0.0', port=5001, debug=False)
    else:
        app.run(debug=True, port=5001)