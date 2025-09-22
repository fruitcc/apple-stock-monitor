#!/bin/bash

# Start Apple Stock Monitor with Web Interface

echo "Starting Apple Stock Monitor with Web Interface..."

# Activate virtual environment if it exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Start the monitor in background
echo "Starting Osaka stores monitor..."
python osaka_stores_monitor.py > monitor.log 2>&1 &
MONITOR_PID=$!
echo "Monitor started with PID: $MONITOR_PID"

# Start Flask web app
echo "Starting web interface on http://127.0.0.1:5000..."
python app.py > flask.log 2>&1 &
FLASK_PID=$!
echo "Flask app started with PID: $FLASK_PID"

echo ""
echo "✅ System is running!"
echo ""
echo "📊 Web Interface: http://127.0.0.1:5001"
echo "📁 Monitor Log: monitor.log"
echo "📁 Flask Log: flask.log"
echo "📁 Database: stock_history.db"
echo ""
echo "To stop all processes:"
echo "  kill $MONITOR_PID $FLASK_PID"
echo "  Or: pkill -f 'python osaka_stores_monitor.py' && pkill -f 'python app.py'"
echo ""
echo "Press Ctrl+C to stop watching the logs..."

# Watch the logs
tail -f monitor.log