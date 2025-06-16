#!/bin/bash

# Script pentru pornirea monitorului de sistem în background

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MONITOR_SCRIPT="$SCRIPT_DIR/real_time_monitor.py"
PID_FILE="/tmp/monitor.pid"
LOG_FILE="/tmp/monitor.log"

start_monitor() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Monitor deja rulează cu PID $PID"
            return 1
        else
            echo "PID file găsit dar procesul nu rulează, curăț..."
            rm -f "$PID_FILE"
        fi
    fi
    
    echo "Pornesc monitorul de sistem..."
    python3 "$MONITOR_SCRIPT" 30 > "$LOG_FILE" 2>&1 &
    
    echo "Monitor pornit cu PID $!"
    echo "Logs: tail -f $LOG_FILE"
}

stop_monitor() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        echo "Opresc monitorul cu PID $PID..."
        kill "$PID" 2>/dev/null
        rm -f "$PID_FILE"
        echo "Monitor oprit"
    else
        echo "Monitor nu rulează"
    fi
}

status_monitor() {
    if [ -f "$PID_FILE" ]; then
        PID=$(cat "$PID_FILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            echo "Monitor rulează cu PID $PID"
            echo "Ultimele logs:"
            tail -5 "$LOG_FILE" 2>/dev/null || echo "Nu există logs"
        else
            echo "PID file există dar procesul nu rulează"
            rm -f "$PID_FILE"
        fi
    else
        echo "Monitor nu rulează"
    fi
}

case "$1" in
    start)
        start_monitor
        ;;
    stop)
        stop_monitor
        ;;
    restart)
        stop_monitor
        sleep 2
        start_monitor
        ;;
    status)
        status_monitor
        ;;
    *)
        echo "Utilizare: $0 {start|stop|restart|status}"
        exit 1
        ;;
esac
