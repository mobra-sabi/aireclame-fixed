#!/bin/bash

echo "🚀 Pornesc AireClame cu monitorizare..."

# Pornește monitorul de sistem în background
echo "📊 Pornesc monitorul de sistem..."
python3 /app/scripts/real_time_monitor.py 30 > /tmp/monitor.log 2>&1 &
MONITOR_PID=$!
echo "Monitor pornit cu PID $MONITOR_PID"

# Pornește aplicația Next.js
echo "🌐 Pornesc aplicația Next.js..."
npm start &
NEXTJS_PID=$!
echo "Next.js pornit cu PID $NEXTJS_PID"

# Funcție pentru oprirea gracioasă
cleanup() {
    echo "🛑 Opresc serviciile..."
    kill $MONITOR_PID 2>/dev/null
    kill $NEXTJS_PID 2>/dev/null
    exit 0
}

# Înregistrează handler pentru semnale
trap cleanup SIGTERM SIGINT

# Așteaptă ca procesele să se termine
wait $NEXTJS_PID
