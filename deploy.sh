#!/bin/bash

# Script de deployment pentru AiReclame pe server cu multiple GPU-uri
set -e

echo "🚀 Starting AiReclame deployment..."

# Verifică dacă Docker și Docker Compose sunt instalate
if ! command -v docker &> /dev/null; then
    echo "❌ Docker nu este instalat. Instalează Docker mai întâi."
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose nu este instalat. Instalează Docker Compose mai întâi."
    exit 1
fi

# Verifică suportul NVIDIA Docker
if ! docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi &> /dev/null; then
    echo "❌ NVIDIA Docker runtime nu este configurat corect."
    echo "Rulează: sudo apt install nvidia-docker2 && sudo systemctl restart docker"
    exit 1
fi

# Creează directoarele necesare
echo "📁 Creez directoarele necesare..."
mkdir -p data/ads logs config ssl

# Verifică fișierul de chei API
if [ ! -f "api_keys.json" ]; then
    echo "📝 Creez fișierul api_keys.json..."
    cat > api_keys.json << EOF
[
    "YOUR_YOUTUBE_API_KEY_1",
    "YOUR_YOUTUBE_API_KEY_2",
    "YOUR_YOUTUBE_API_KEY_3"
]
EOF
    echo "⚠️  Editează api_keys.json cu cheile tale YouTube API!"
fi

# Verifică numărul de GPU-uri disponibile
GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
echo "🎮 Detectate $GPU_COUNT GPU-uri"

# Actualizează docker-compose.yml cu numărul corect de GPU-uri
if [ $GPU_COUNT -gt 0 ]; then
    GPU_LIST=$(seq -s, 0 $((GPU_COUNT-1)))
    sed -i "s/CUDA_VISIBLE_DEVICES=0,1,2,3/CUDA_VISIBLE_DEVICES=$GPU_LIST/g" docker-compose.yml
    echo "✅ Configurat pentru $GPU_COUNT GPU-uri: $GPU_LIST"
fi

# Build și start containers
echo "🔨 Building containers..."
docker-compose build --no-cache

echo "🚀 Starting services..."
docker-compose up -d

# Așteaptă ca serviciile să pornească
echo "⏳ Aștept ca serviciile să pornească..."
sleep 30

# Verifică statusul serviciilor
echo "📊 Status servicii:"
docker-compose ps

# Inițializează baza de date
echo "🗄️  Inițializez baza de date..."
docker-compose exec aireclame-app node -e "
const fs = require('fs');
const path = require('path');
const dbPath = '/data/ads/ads_database.db';
const dbDir = path.dirname(dbPath);
if (!fs.existsSync(dbDir)) {
    fs.mkdirSync(dbDir, { recursive: true });
}
console.log('Database directory created');
"

# Afișează informații de conectare
echo ""
echo "🎉 Deployment complet!"
echo ""
echo "📱 Aplicația este disponibilă la:"
echo "   - Local: http://localhost"
echo "   - Tailscale: http://$(tailscale ip -4):80"
echo ""
echo "📊 Monitorizare:"
echo "   - Logs aplicație: docker-compose logs -f aireclame-app"
echo "   - Logs crawler: docker-compose logs -f aireclame-crawler"
echo "   - Status GPU: nvidia-smi"
echo ""
echo "🔧 Comenzi utile:"
echo "   - Stop: docker-compose down"
echo "   - Restart: docker-compose restart"
echo "   - Update: git pull && docker-compose build && docker-compose up -d"
echo ""

# Afișează IP-ul Tailscale dacă este disponibil
if command -v tailscale &> /dev/null; then
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "Nu este conectat")
    echo "🔗 IP Tailscale: $TAILSCALE_IP"
fi
