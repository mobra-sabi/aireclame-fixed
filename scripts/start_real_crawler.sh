#!/bin/bash

# Script pentru crawler-ul REAL YouTube - FĂRĂ DATE FAKE

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CRAWLER_SCRIPT="$SCRIPT_DIR/real_youtube_crawler.py"
PID_FILE="/tmp/real_crawler.pid"
LOG_FILE="/tmp/real_crawler.log"

start_crawler() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "❌ Real crawler already running with PID $PID"
            return 1
        else
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "🚀 Starting REAL YouTube crawler..."
    echo "📊 Logs: tail -f $LOG_FILE"
    echo "🔑 Using REAL YouTube API keys"
    
    # Setează variabilele de mediu
    export DATABASE_PATH="/data/ads/real_ads.db"
    export PYTHONPATH="$SCRIPT_DIR/.."
    
    # Creează directorul pentru baza de date
    mkdir -p "$(dirname "$DATABASE_PATH")"
    
    # Pornește crawler-ul REAL
    cd "$SCRIPT_DIR/.."
    nohup python3 "$CRAWLER_SCRIPT" > "$LOG_FILE" 2>&1 &
    CRAWLER_PID=$!
    
    sleep 3
    
    if ps -p "$CRAWLER_PID" > /dev/null 2>&1; then
        echo "✅ REAL crawler started successfully!"
        echo "🆔 PID: $CRAWLER_PID"
        echo "💾 Database: $DATABASE_PATH"
        echo "📋 Logs: $LOG_FILE"
        echo ""
        echo "📈 Monitor progress:"
        echo "   tail -f $LOG_FILE"
        echo ""
        echo "🛑 To stop:"
        echo "   $0 stop"
    else
        echo "❌ Failed to start real crawler! Check logs:"
        echo "   tail $LOG_FILE"
        return 1
    fi
}

stop_crawler() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "🛑 Stopping real crawler with PID $PID..."
        kill "$PID" 2>/dev/null
        
        for i in {1..10}; do
            if ! ps -p "$PID" > /dev/null 2>&1; then
                break
            fi
            sleep 1
        done
        
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "⚡ Force stopping..."
            kill -9 "$PID" 2>/dev/null
        fi
        
        rm -f "$PID_FILE"
        echo "✅ Real crawler stopped"
    else
        echo "ℹ️  Real crawler not running"
    fi
}

status_crawler() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "✅ REAL crawler running with PID $PID"
            echo ""
            echo "📊 Recent activity:"
            if [ -f "$LOG_FILE" ]; then
                echo "$(tail -10 "$LOG_FILE" | grep -E "(Found|Saved|completed)" | tail -5)"
            fi
            echo ""
            echo "💾 Real database:"
            DB_PATH="/data/ads/real_ads.db"
            if [ -f "$DB_PATH" ]; then
                DB_SIZE=$(du -h "$DB_PATH" | cut -f1)
                echo "   Size: $DB_SIZE"
                
                if command -v sqlite3 >/dev/null 2>&1; then
                    ADS_COUNT=$(sqlite3 "$DB_PATH" "SELECT COUNT(*) FROM real_ads;" 2>/dev/null || echo "N/A")
                    echo "   Real ads found: $ADS_COUNT"
                fi
            else
                echo "   Database not created yet"
            fi
        else
            echo "❌ PID file exists but process not running"
            rm -f "$PID_FILE"
        fi
    else
        echo "⏹️  REAL crawler not running"
    fi
}

logs_crawler() {
    if [ -f "$LOG_FILE" ]; then
        echo "📋 Following REAL crawler logs (Ctrl+C to exit):"
        tail -f "$LOG_FILE"
    else
        echo "📋 No logs yet"
    fi
}

case "$1" in
    start)
        start_crawler
        ;;
    stop)
        stop_crawler
        ;;
    restart)
        stop_crawler
        sleep 2
        start_crawler
        ;;
    status)
        status_crawler
        ;;
    logs)
        logs_crawler
        ;;
    *)
        echo "🔧 Usage: $0 {start|stop|restart|status|logs}"
        echo ""
        echo "REAL YouTube Crawler Commands:"
        echo "  start   - Start REAL crawler with your API keys"
        echo "  stop    - Stop REAL crawler"
        echo "  restart - Restart REAL crawler"
        echo "  status  - Show REAL crawler status"
        echo "  logs    - Follow REAL crawler logs"
        echo ""
        echo "🔑 Uses REAL YouTube API keys - NO FAKE DATA!"
        exit 1
        ;;
esac
