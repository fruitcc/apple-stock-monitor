#!/usr/bin/env python3

from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta
import sqlite3
from database import StockDatabase

app = Flask(__name__)
db = StockDatabase()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/api/current-status')
def get_current_status():
    """Get current availability status for all products and stores"""
    status = db.get_current_status()
    return jsonify(status)

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

@app.template_filter('format_datetime')
def format_datetime(value):
    """Format datetime for display"""
    if value:
        dt = datetime.fromisoformat(value)
        return dt.strftime('%Y-%m-%d %H:%M:%S')
    return ''

@app.template_filter('time_ago')
def time_ago(value):
    """Convert datetime to 'time ago' format"""
    if not value:
        return 'never'

    dt = datetime.fromisoformat(value)
    now = datetime.now()
    diff = now - dt

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
        app.run(host='0.0.0.0', port=5000, debug=False)
    else:
        app.run(debug=True, port=5000)