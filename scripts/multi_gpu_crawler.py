#!/usr/bin/env python3
"""
Crawler optimizat pentru multiple GPU-uri
"""

import torch
import torch.multiprocessing as mp
from torch.nn.parallel import DistributedDataParallel
import os
import asyncio
from concurrent.futures import ProcessPoolExecutor
import logging
from improved_crawler import YouTubeCrawler, Config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MultiGPUCrawler:
    def __init__(self, config: Config):
        self.config = config
        self.gpu_count = torch.cuda.device_count()
        logger.info(f"🎮 Detectate {self.gpu_count} GPU-uri")
        
    def setup_gpu_worker(self, gpu_id, video_batch):
        """Configurează un worker pentru un GPU specific"""
        torch.cuda.set_device(gpu_id)
        device = torch.device(f'cuda:{gpu_id}')
        
        logger.info(f"🚀 Worker GPU {gpu_id} procesează {len(video_batch)} videoclipuri")
        
        # Creează crawler pentru acest GPU
        crawler = YouTubeCrawler(self.config)
        
        # Procesează batch-ul de videoclipuri
        results = []
        for video_data in video_batch:
            try:
                # Aici ai putea adăuga procesarea specifică GPU
                result = asyncio.run(crawler.process_video_async(video_data))
                results.append(result)
            except Exception as e:
                logger.error(f"Eroare procesare video pe GPU {gpu_id}: {e}")
        
        return results
    
    def distribute_videos(self, videos):
        """Distribuie videoclipurile pe GPU-uri"""
        if self.gpu_count == 0:
            logger.warning("Nu sunt GPU-uri disponibile, folosesc CPU")
            return [videos]
        
        batch_size = len(videos) // self.gpu_count
        batches = []
        
        for i in range(self.gpu_count):
            start_idx = i * batch_size
            if i == self.gpu_count - 1:  # Ultimul batch ia restul
                end_idx = len(videos)
            else:
                end_idx = (i + 1) * batch_size
            
            batch = videos[start_idx:end_idx]
            if batch:  # Doar dacă batch-ul nu e gol
                batches.append(batch)
        
        return batches
    
    async def crawl_with_multiple_gpus(self, query, max_results=None):
        """Crawling cu multiple GPU-uri"""
        logger.info(f"🔍 Încep crawling cu {self.gpu_count} GPU-uri pentru: {query}")
        
        # Obține lista de videoclipuri
        crawler = YouTubeCrawler(self.config)
        
        # Simulez obținerea videoclipurilor (în realitate ar veni din YouTube API)
        videos = []  # Aici ar fi lista reală de videoclipuri
        
        if not videos:
            logger.warning("Nu s-au găsit videoclipuri pentru procesare")
            return
        
        # Distribuie videoclipurile pe GPU-uri
        video_batches = self.distribute_videos(videos)
        
        if self.gpu_count > 0:
            # Procesare paralelă pe multiple GPU-uri
            with ProcessPoolExecutor(max_workers=self.gpu_count) as executor:
                futures = []
                for gpu_id, batch in enumerate(video_batches):
                    future = executor.submit(self.setup_gpu_worker, gpu_id, batch)
                    futures.append(future)
                
                # Așteaptă rezultatele
                results = []
                for future in futures:
                    try:
                        result = future.result(timeout=3600)  # 1 oră timeout
                        results.extend(result)
                    except Exception as e:
                        logger.error(f"Eroare în procesarea GPU: {e}")
        else:
            # Fallback la CPU
            logger.info("Folosesc CPU pentru procesare")
            crawler = YouTubeCrawler(self.config)
            for video_data in videos:
                await crawler.process_video_async(video_data)

def optimize_gpu_memory():
    """Optimizează utilizarea memoriei GPU"""
    if torch.cuda.is_available():
        for i in range(torch.cuda.device_count()):
            torch.cuda.set_device(i)
            torch.cuda.empty_cache()
            
            # Setează memory fraction pentru a evita out-of-memory
            torch.cuda.set_per_process_memory_fraction(0.8, device=i)
            
        logger.info(f"✅ Optimizat memoria pentru {torch.cuda.device_count()} GPU-uri")

async def main():
    """Funcția principală pentru crawling multi-GPU"""
    # Optimizează memoria GPU
    optimize_gpu_memory()
    
    # Configurare
    config = Config()
    config.MAX_WORKERS = torch.cuda.device_count() * 2  # 2 workers per GPU
    
    # Creează crawler multi-GPU
    multi_crawler = MultiGPUCrawler(config)
    
    # Queries pentru căutare
    queries = [
        "reclamă 2025 OR advertisement 2025 OR ad 2025 OR commercial 2025",
        "publicitate România 2025",
        "marketing campaign 2025"
    ]
    
    # Rulează crawling-ul pentru fiecare query
    for query in queries:
        try:
            await multi_crawler.crawl_with_multiple_gpus(query, max_results=200)
            logger.info(f"✅ Completat crawling pentru query: {query}")
        except Exception as e:
            logger.error(f"❌ Eșuat crawling pentru query '{query}': {e}")

if __name__ == "__main__":
    # Setează variabile de mediu pentru PyTorch
    os.environ['CUDA_LAUNCH_BLOCKING'] = '1'
    os.environ['TORCH_USE_CUDA_DSA'] = '1'
    
    # Rulează crawling-ul
    asyncio.run(main())
