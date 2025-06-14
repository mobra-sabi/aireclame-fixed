# Multi-stage build pentru optimizare
FROM nvidia/cuda:12.1-devel-ubuntu22.04 as base

# Setează variabile de mediu
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV NODE_VERSION=20

# Instalează dependențe de sistem
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    ffmpeg \
    curl \
    wget \
    git \
    build-essential \
    sqlite3 \
    htop \
    psutil \
    && rm -rf /var/lib/apt/lists/*

# Instalează Node.js
RUN curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | bash - \
    && apt-get install -y nodejs

# Instalează yt-dlp
RUN pip3 install yt-dlp

# Creează directorul de lucru
WORKDIR /app

# Copiază requirements pentru Python
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Instalează psutil pentru monitorizare
RUN pip3 install psutil

# Copiază package.json pentru Node.js
COPY package*.json ./
RUN npm ci --only=production

# Copiază codul aplicației
COPY . .

# Build Next.js app
RUN npm run build

# Creează directoarele necesare
RUN mkdir -p /data/ads /tmp/crawler /tmp/logs

# Setează permisiuni
RUN chmod +x scripts/*.py scripts/*.sh

# Expune portul
EXPOSE 3000

# Script de start care pornește și monitorul
COPY scripts/docker-start.sh /docker-start.sh
RUN chmod +x /docker-start.sh

# Comandă de start
CMD ["/docker-start.sh"]
