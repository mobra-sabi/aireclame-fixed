#!/usr/bin/env python3
"""
Monitor pentru utilizarea GPU-urilor în timpul procesării
"""

import time
import subprocess
import json
import psutil
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GPUMonitor:
    def __init__(self, interval=5):
        self.interval = interval
        self.running = False
        
    def get_gpu_info(self):
        """Obține informații despre GPU-uri"""
        try:
            result = subprocess.run([
                'nvidia-smi', 
                '--query-gpu=index,name,memory.used,memory.total,utilization.gpu,temperature.gpu,power.draw',
                '--format=csv,noheader,nounits'
            ], capture_output=True, text=True, check=True)
            
            gpus = []
            for line in result.stdout.strip().split('\n'):
                if line:
                    parts = [p.strip() for p in line.split(',')]
                    gpus.append({
                        'index': int(parts[0]),
                        'name': parts[1],
                        'memory_used': int(parts[2]),
                        'memory_total': int(parts[3]),
                        'utilization': int(parts[4]),
                        'temperature': int(parts[5]),
                        'power_draw': float(parts[6]) if parts[6] != '[N/A]' else 0
                    })
            return gpus
        except subprocess.CalledProcessError:
            logger.error("Nu s-au putut obține informații GPU")
            return []
    
    def get_system_info(self):
        """Obține informații despre sistem"""
        return {
            'cpu_percent': psutil.cpu_percent(),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_usage': psutil.disk_usage('/').percent,
            'timestamp': datetime.now().isoformat()
        }
    
    def log_stats(self):
        """Loghează statisticile"""
        gpus = self.get_gpu_info()
        system = self.get_system_info()
        
        print(f"\n{'='*60}")
        print(f"📊 Monitor AiReclame - {system['timestamp']}")
        print(f"{'='*60}")
        
        # Informații sistem
        print(f"🖥️  CPU: {system['cpu_percent']:.1f}% | "
              f"RAM: {system['memory_percent']:.1f}% | "
              f"Disk: {system['disk_usage']:.1f}%")
        
        # Informații GPU
        if gpus:
            print(f"\n🎮 GPU Status:")
            for gpu in gpus:
                memory_percent = (gpu['memory_used'] / gpu['memory_total']) * 100
                print(f"   GPU {gpu['index']}: {gpu['name']}")
                print(f"   ├─ Utilizare: {gpu['utilization']}%")
                print(f"   ├─ Memorie: {gpu['memory_used']}MB/{gpu['memory_total']}MB ({memory_percent:.1f}%)")
                print(f"   ├─ Temperatură: {gpu['temperature']}°C")
                print(f"   └─ Putere: {gpu['power_draw']:.1f}W")
        else:
            print("❌ Nu s-au detectat GPU-uri NVIDIA")
        
        # Procesele active
        try:
            result = subprocess.run(['docker-compose', 'ps'], 
                                  capture_output=True, text=True, check=True)
            print(f"\n🐳 Docker Status:")
            for line in result.stdout.split('\n')[2:]:  # Skip header
                if line.strip():
                    print(f"   {line}")
        except:
            pass
    
    def start_monitoring(self):
        """Începe monitorizarea"""
        self.running = True
        logger.info(f"🚀 Pornesc monitorizarea GPU cu interval {self.interval}s")
        
        try:
            while self.running:
                self.log_stats()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("⏹️  Opresc monitorizarea")
            self.running = False

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitor GPU pentru AiReclame')
    parser.add_argument('--interval', type=int, default=5, 
                       help='Interval de monitorizare în secunde (default: 5)')
    
    args = parser.parse_args()
    
    monitor = GPUMonitor(interval=args.interval)
    monitor.start_monitoring()
