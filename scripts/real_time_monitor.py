#!/usr/bin/env python3
"""
Monitor în timp real pentru sistemul AireClame
Colectează și salvează metrici de sistem la fiecare 30 de secunde
"""

import time
import json
import sqlite3
import psutil
import subprocess
import logging
from datetime import datetime
import os
import signal
import sys

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/monitor.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class SystemMonitor:
    def __init__(self):
        self.running = False
        self.db_path = os.getenv('DATABASE_PATH', '/data/ads/ads_database.db')
        self.metrics_file = '/tmp/system_metrics.json'
        
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
                    if len(parts) >= 6:
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
        except (subprocess.CalledProcessError, FileNotFoundError):
            logger.warning("nvidia-smi nu este disponibil")
            return []
    
    def get_system_metrics(self):
        """Colectează metrici de sistem"""
        try:
            # CPU și memorie
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Procese active
            processes = []
            for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent']):
                try:
                    pinfo = proc.info
                    if pinfo['cpu_percent'] > 0.1:  # Doar procesele active
                        processes.append({
                            'pid': pinfo['pid'],
                            'name': pinfo['name'],
                            'cpu': pinfo['cpu_percent'],
                            'memory': pinfo['memory_percent']
                        })
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    pass
            
            # Sortează după utilizarea CPU
            processes.sort(key=lambda x: x['cpu'], reverse=True)
            
            # GPU info
            gpus = self.get_gpu_info()
            
            metrics = {
                'timestamp': datetime.now().isoformat(),
                'cpu_usage': cpu_percent,
                'memory_usage': memory.percent,
                'storage_usage': disk.percent,
                'active_processes': len([p for p in processes if p['cpu'] > 1.0]),
                'gpus': gpus,
                'processes': processes[:10],  # Top 10 procese
                'system_load': os.getloadavg() if hasattr(os, 'getloadavg') else [0, 0, 0]
            }
            
            return metrics
            
        except Exception as e:
            logger.error(f"Eroare colectare metrici: {e}")
            return None
    
    def save_metrics(self, metrics):
        """Salvează metricile în fișier JSON pentru acces rapid"""
        try:
            with open(self.metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
        except Exception as e:
            logger.error(f"Eroare salvare metrici: {e}")
    
    def save_to_database(self, metrics):
        """Salvează metricile în baza de date pentru istoric"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Creează tabela dacă nu există
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS system_metrics (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT,
                        cpu_usage REAL,
                        memory_usage REAL,
                        storage_usage REAL,
                        active_processes INTEGER,
                        gpu_data TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Inserează metricile
                cursor.execute("""
                    INSERT INTO system_metrics 
                    (timestamp, cpu_usage, memory_usage, storage_usage, active_processes, gpu_data)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    metrics['timestamp'],
                    metrics['cpu_usage'],
                    metrics['memory_usage'],
                    metrics['storage_usage'],
                    metrics['active_processes'],
                    json.dumps(metrics['gpus'])
                ))
                
                # Păstrează doar ultimele 1000 de înregistrări
                cursor.execute("""
                    DELETE FROM system_metrics 
                    WHERE id NOT IN (
                        SELECT id FROM system_metrics 
                        ORDER BY created_at DESC 
                        LIMIT 1000
                    )
                """)
                
        except Exception as e:
            logger.error(f"Eroare salvare în baza de date: {e}")
    
    def signal_handler(self, signum, frame):
        """Handler pentru oprirea gracioasă"""
        logger.info("Primind semnal de oprire...")
        self.running = False
    
    def start_monitoring(self, interval=30):
        """Începe monitorizarea"""
        self.running = True
        
        # Înregistrează handler-ele pentru semnale
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        logger.info(f"Pornesc monitorizarea cu interval {interval}s")
        
        # Salvează PID-ul pentru control
        with open('/tmp/monitor.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            while self.running:
                metrics = self.get_system_metrics()
                
                if metrics:
                    # Salvează în fișier pentru acces rapid
                    self.save_metrics(metrics)
                    
                    # Salvează în baza de date pentru istoric
                    self.save_to_database(metrics)
                    
                    logger.info(f"Metrici colectate: CPU {metrics['cpu_usage']:.1f}%, "
                              f"RAM {metrics['memory_usage']:.1f}%, "
                              f"GPU-uri {len(metrics['gpus'])}")
                
                # Așteaptă următorul interval
                for _ in range(interval):
                    if not self.running:
                        break
                    time.sleep(1)
                    
        except Exception as e:
            logger.error(f"Eroare în bucla de monitorizare: {e}")
        finally:
            # Curăță PID file
            try:
                os.remove('/tmp/monitor.pid')
            except:
                pass
            logger.info("Monitorizarea s-a oprit")

def main():
    monitor = SystemMonitor()
    
    # Verifică argumentele
    interval = 30
    if len(sys.argv) > 1:
        try:
            interval = int(sys.argv[1])
        except ValueError:
            logger.error("Intervalul trebuie să fie un număr întreg")
            sys.exit(1)
    
    monitor.start_monitoring(interval)

if __name__ == "__main__":
    main()
