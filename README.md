# 🚀 AiReclame - AI-Powered YouTube Ads Analytics

Sistem avansat de crawling și analiză a reclamelor YouTube folosind AI și multiple GPU-uri.

## 🎮 Cerințe Sistem

### Hardware
- **GPU**: 1+ NVIDIA GPU-uri cu CUDA support
- **RAM**: Minim 16GB (recomandat 32GB+)
- **Storage**: Minim 100GB SSD
- **CPU**: 8+ cores recomandat

### Software
- Ubuntu 22.04 LTS
- NVIDIA Drivers 535+
- Docker & Docker Compose
- CUDA 12.1+
- Tailscale (pentru acces remote)

## 🛠️ Instalare Rapidă

### 1. Setup Server
\`\`\`bash
# Rulează script-ul de setup automat
chmod +x setup_server.sh
./setup_server.sh

# Conectează la Tailscale
sudo tailscale up
\`\`\`

### 2. Configurare Aplicație
\`\`\`bash
# Clonează/copiază codul în ~/aireclame
cd ~/aireclame

# Editează cheile API
nano api_keys.json

# Deploy aplicația
chmod +x deploy.sh
./deploy.sh
\`\`\`

### 3. Acces Aplicație
- **Local**: http://localhost
- **Tailscale**: http://[tailscale-ip]
- **Setup**: http://[ip]/setup

## 📊 Monitorizare

### GPU Monitoring
\`\`\`bash
# Monitor în timp real
python3 scripts/gpu_monitor.py

# NVIDIA SMI
watch -n 1 nvidia-smi

# Logs aplicație
docker-compose logs -f aireclame-app
docker-compose logs -f aireclame-crawler
\`\`\`

### System Status
\`\`\`bash
# Status containere
docker-compose ps

# Utilizare resurse
htop
nvtop  # Pentru GPU-uri
\`\`\`

## 🚀 Utilizare

### 1. Configurare Inițială
1. Accesează `/setup` pentru inițializarea bazei de date
2. Adaugă cheile YouTube API în `api_keys.json`
3. Configurează parametrii în dashboard

### 2. Crawling Manual
\`\`\`bash
# Crawler simplu
docker-compose exec aireclame-crawler python3 scripts/improved_crawler.py

# Crawler multi-GPU
docker-compose exec aireclame-crawler python3 scripts/multi_gpu_crawler.py
\`\`\`

### 3. Programare Automată
\`\`\`bash
# Adaugă în crontab pentru crawling automat
crontab -e

# Exemplu: crawling la fiecare 6 ore
0 */6 * * * cd ~/aireclame && docker-compose exec -T aireclame-crawler python3 scripts/improved_crawler.py
\`\`\`

## 🔧 Configurare Avansată

### Multiple GPU-uri
Editează `docker-compose.yml`:
\`\`\`yaml
environment:
  - CUDA_VISIBLE_DEVICES=0,1,2,3  # Pentru 4 GPU-uri
\`\`\`

### Optimizare Performanță
\`\`\`bash
# Setează memory fraction pentru GPU
export PYTORCH_CUDA_ALLOC_CONF=max_split_size_mb:512

# Optimizează pentru multiple workers
export OMP_NUM_THREADS=4
\`\`\`

### SSL/HTTPS
1. Obține certificat SSL
2. Plasează în `./ssl/`
3. Decomentează liniile SSL din `nginx.conf`

## 📈 Funcționalități

### ✅ Implementate
- [x] Crawling YouTube cu API rotation
- [x] Analiză audio avansată (tempo, energie, MFCC)
- [x] Analiză vizuală (culori, text density)
- [x] Dashboard interactiv
- [x] Suport multiple GPU-uri
- [x] Containerizare Docker
- [x] Monitoring în timp real

### 🔄 În Dezvoltare
- [ ] Machine Learning classification
- [ ] Export date (CSV, Excel)
- [ ] Alerting system
- [ ] API REST complet
- [ ] Suport pentru alte platforme (TikTok, Instagram)

## 🐛 Troubleshooting

### GPU Issues
\`\`\`bash
# Verifică drivers NVIDIA
nvidia-smi

# Restart Docker cu GPU support
sudo systemctl restart docker

# Test GPU în container
docker run --rm --gpus all nvidia/cuda:12.1-base-ubuntu22.04 nvidia-smi
\`\`\`

### Database Issues
\`\`\`bash
# Reset database
rm -rf data/ads/ads_database.db
docker-compose restart aireclame-app
# Accesează /setup pentru reinițializare
\`\`\`

### Performance Issues
\`\`\`bash
# Verifică utilizarea resurselor
docker stats

# Optimizează memoria GPU
docker-compose exec aireclame-crawler python3 -c "
import torch
torch.cuda.empty_cache()
print('GPU memory cleared')
"
\`\`\`

## 📞 Support

Pentru probleme sau întrebări:
1. Verifică logs: `docker-compose logs`
2. Monitorizează GPU: `nvidia-smi`
3. Verifică conectivitatea: `tailscale status`

## 📄 Licență

MIT License - Vezi fișierul LICENSE pentru detalii.
