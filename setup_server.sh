#!/bin/bash

# Script de setup pentru server Ubuntu cu multiple GPU-uri
set -e

echo "🚀 Configurez serverul pentru AiReclame..."

# Update sistem
echo "📦 Actualizez sistemul..."
sudo apt update && sudo apt upgrade -y

# Instalează dependențe de bază
echo "🔧 Instalez dependențe de bază..."
sudo apt install -y \
    curl \
    wget \
    git \
    htop \
    nvtop \
    tree \
    unzip \
    software-properties-common \
    apt-transport-https \
    ca-certificates \
    gnupg \
    lsb-release

# Instalează Docker
echo "🐳 Instalez Docker..."
if ! command -v docker &> /dev/null; then
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt update
    sudo apt install -y docker-ce docker-ce-cli containerd.io docker-compose-plugin
    sudo usermod -aG docker $USER
    echo "✅ Docker instalat"
else
    echo "✅ Docker deja instalat"
fi

# Instalează Docker Compose
echo "🔧 Instalez Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo "✅ Docker Compose instalat"
else
    echo "✅ Docker Compose deja instalat"
fi

# Verifică și instalează NVIDIA drivers
echo "🎮 Verific NVIDIA drivers..."
if ! command -v nvidia-smi &> /dev/null; then
    echo "⚠️  NVIDIA drivers nu sunt instalați. Instalez..."
    sudo apt install -y nvidia-driver-535 nvidia-utils-535
    echo "🔄 Restart necesar pentru NVIDIA drivers"
else
    echo "✅ NVIDIA drivers detectați"
    nvidia-smi
fi

# Instalează NVIDIA Docker runtime
echo "🐳 Instalez NVIDIA Docker runtime..."
if ! docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi &> /dev/null 2>&1; then
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
    sudo apt update
    sudo apt install -y nvidia-docker2
    sudo systemctl restart docker
    echo "✅ NVIDIA Docker runtime instalat"
else
    echo "✅ NVIDIA Docker runtime deja configurat"
fi

# Instalează Tailscale (dacă nu e deja instalat)
echo "🔗 Verific Tailscale..."
if ! command -v tailscale &> /dev/null; then
    echo "📡 Instalez Tailscale..."
    curl -fsSL https://tailscale.com/install.sh | sh
    echo "⚠️  Rulează 'sudo tailscale up' pentru a conecta la rețea"
else
    echo "✅ Tailscale deja instalat"
    tailscale status
fi

# Configurează firewall
echo "🔥 Configurez firewall..."
sudo ufw allow ssh
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw allow in on tailscale0
sudo ufw --force enable

# Creează directorul pentru aplicație
echo "📁 Creez directorul aplicației..."
mkdir -p ~/aireclame
cd ~/aireclame

# Clonează repository-ul (dacă nu există)
if [ ! -d ".git" ]; then
    echo "📥 Clonez codul aplicației..."
    # Aici ar trebui să clonezi din repository-ul tău
    echo "⚠️  Copiază codul aplicației în ~/aireclame/"
fi

# Setează permisiuni
echo "🔐 Setez permisiuni..."
chmod +x *.sh
chmod +x scripts/*.py

# Afișează informații finale
echo ""
echo "🎉 Setup server complet!"
echo ""
echo "📋 Următorii pași:"
echo "1. Copiază codul aplicației în ~/aireclame/"
echo "2. Editează api_keys.json cu cheile YouTube API"
echo "3. Rulează ./deploy.sh pentru a porni aplicația"
echo ""
echo "🔧 Comenzi utile:"
echo "   - Status GPU: nvidia-smi"
echo "   - Monitor GPU: watch -n 1 nvidia-smi"
echo "   - Status Docker: docker ps"
echo "   - Logs: docker-compose logs -f"
echo ""

# Afișează informații despre sistem
echo "💻 Informații sistem:"
echo "   - CPU: $(nproc) cores"
echo "   - RAM: $(free -h | awk '/^Mem:/ {print $2}')"
echo "   - GPU: $(nvidia-smi --list-gpus | wc -l) NVIDIA GPU(s)"
echo "   - Disk: $(df -h / | awk 'NR==2 {print $4}') free"

if command -v tailscale &> /dev/null; then
    TAILSCALE_IP=$(tailscale ip -4 2>/dev/null || echo "Nu este conectat")
    echo "   - Tailscale IP: $TAILSCALE_IP"
fi
