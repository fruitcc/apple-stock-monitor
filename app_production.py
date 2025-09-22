#!/usr/bin/env python3

from app import app
import logging
from logging.handlers import RotatingFileHandler
import os

if __name__ == '__main__':
    # Setup production logging
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler('logs/flask_app.log', maxBytes=10240000, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('Apple Stock Monitor Web Dashboard startup')

    # Run in production mode
    # Listen on all interfaces for VPS deployment
    app.run(host='0.0.0.0', port=5000, debug=False)