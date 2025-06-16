import os
import sqlite3
import subprocess
import logging
import json
import librosa
import numpy as np
import torch
import torchaudio
from scipy.signal import correlate
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from contextlib import contextmanager
import psutil
from datetime import datetime
import cv2
from PIL import Image
import requests

# Configurare logging îmbunătățită
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('ad_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class Config:
    MAX_RESULTS: int = 200
    AUDIO_DURATION: int = 30
    DOWNLOAD_TIMEOUT: int = 60
    MAX_RETRIES: int = 3
    DATABASE_PATH: str = '/data/ads/ads_database.db'
    TEMP_DIR: str = '/tmp'
    MAX_WORKERS: int = 4
    RATE_LIMIT_CALLS_PER_MINUTE: int = 100

class CrawlerMetrics:
    def __init__(self):
        self.start_time = datetime.now()
        self.videos_processed = 0
        self.videos_failed = 0
        self.total_download_time = 0
        self.errors = []
    
    def log_progress(self):
        elapsed = datetime.now() - self.start_time
        success_rate = (self.videos_processed / (self.videos_processed + self.videos_failed)) * 100 if (self.videos_processed + self.videos_failed) > 0 else 0
        
        logger.info(f"Progress: {self.videos_processed} processed, {self.videos_failed} failed")
        logger.info(f"Success rate: {success_rate:.2f}%")
        logger.info(f"Elapsed time: {elapsed}")
        
        # System stats
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        logger.info(f"System - CPU: {cpu_percent}%, Memory: {memory.percent}%")

@contextmanager
def temp_file_cleanup(*files):
    try:
        yield
    finally:
        for file in files:
            if os.path.exists(file):
                try:
                    os.remove(file)
                    logger.debug(f"Cleaned up {file}")
                except Exception as e:
                    logger.warning(f"Failed to cleanup {file}: {e}")

class YouTubeCrawler:
    def __init__(self, config: Config):
        self.config = config
        self.metrics = CrawlerMetrics()
        self.api_keys = self._load_api_keys()
        self.youtube = self._get_youtube_service()
        
    def _load_api_keys(self):
        try:
            with open('api_keys.json', 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            logger.error("api_keys.json not found")
            return []
    
    def _get_youtube_service(self):
        for key in self.api_keys:
            try:
                return build('youtube', 'v3', developerKey=key)
            except HttpError as e:
                logger.warning(f"API key failed: {key[:10]}..., error: {e}")
                continue
        raise Exception("No valid API keys available")
    
    def analyze_audio_advanced(self, audio_file):
        """Analiză audio avansată cu mai multe caracteristici"""
        try:
            # Încărcare audio cu librosa
            y, sr = librosa.load(audio_file, duration=self.config.AUDIO_DURATION)
            
            if len(y) == 0:
                return None
            
            # Caracteristici de bază
            tempo, beats = librosa.beat.beat_track(y=y, sr=sr)
            
            # Caracteristici spectrale
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
            spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
            
            # MFCC pentru recunoașterea vocii
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Chroma pentru analiza armonică
            chroma = librosa.feature.chroma_stft(y=y, sr=sr)
            
            # Zero crossing rate pentru detectarea vocii
            zcr = librosa.feature.zero_crossing_rate(y)
            
            # Energie RMS
            rms = librosa.feature.rms(y=y)
            
            # Detectare vorbire vs muzică
            speech_ratio = self._detect_speech_ratio(y, sr)
            
            features = {
                'tempo': float(tempo),
                'energy': float(np.mean(rms)),
                'spectral_centroid': float(np.mean(spectral_centroids)),
                'spectral_rolloff': float(np.mean(spectral_rolloff)),
                'spectral_bandwidth': float(np.mean(spectral_bandwidth)),
                'mfcc_mean': np.mean(mfccs, axis=1).tolist(),
                'chroma_mean': np.mean(chroma, axis=1).tolist(),
                'zero_crossing_rate': float(np.mean(zcr)),
                'speech_ratio': speech_ratio,
                'duration': len(y) / sr
            }
            
            logger.info(f"Audio analysis completed: tempo={tempo:.2f}, energy={features['energy']:.4f}")
            return features
            
        except Exception as e:
            logger.error(f"Audio analysis failed: {e}")
            return None
    
    def _detect_speech_ratio(self, y, sr):
        """Detectează raportul vorbire/muzică în audio"""
        try:
            # Folosim spectral features pentru a diferenția vorbirea de muzică
            spectral_centroids = librosa.feature.spectral_centroid(y=y, sr=sr)
            mfccs = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
            
            # Vorbirea tinde să aibă variabilitate mai mare în spectral centroid
            centroid_var = np.var(spectral_centroids)
            
            # Vorbirea are pattern-uri distinctive în MFCC
            mfcc_var = np.mean(np.var(mfccs, axis=1))
            
            # Heuristică simplă pentru detectarea vorbirii
            speech_score = (centroid_var / 1000000) + (mfcc_var / 100)
            speech_ratio = min(1.0, max(0.0, speech_score))
            
            return speech_ratio
        except:
            return 0.5  # Fallback
    
    def extract_thumbnail_features(self, video_id):
        """Extrage caracteristici din thumbnail-ul video"""
        try:
            # Descarcă thumbnail-ul
            thumbnail_url = f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg"
            response = requests.get(thumbnail_url, timeout=10)
            
            if response.status_code == 200:
                # Salvează temporar imaginea
                thumbnail_path = f"{self.config.TEMP_DIR}/{video_id}_thumb.jpg"
                with open(thumbnail_path, 'wb') as f:
                    f.write(response.content)
                
                # Analizează imaginea
                img = cv2.imread(thumbnail_path)
                if img is not None:
                    # Culori dominante
                    dominant_colors = self._extract_dominant_colors(img)
                    
                    # Detectare text (OCR simplu)
                    text_density = self._estimate_text_density(img)
                    
                    # Brightness și contrast
                    brightness = np.mean(cv2.cvtColor(img, cv2.COLOR_BGR2GRAY))
                    
                    os.remove(thumbnail_path)
                    
                    return {
                        'dominant_colors': dominant_colors,
                        'text_density': text_density,
                        'brightness': float(brightness)
                    }
                
                os.remove(thumbnail_path)
            
        except Exception as e:
            logger.warning(f"Thumbnail analysis failed for {video_id}: {e}")
        
        return None
    
    def _extract_dominant_colors(self, img, k=5):
        """Extrage culorile dominante din imagine"""
        try:
            # Reshape imaginea pentru k-means
            data = img.reshape((-1, 3))
            data = np.float32(data)
            
            # K-means clustering
            criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 20, 1.0)
            _, labels, centers = cv2.kmeans(data, k, None, criteria, 10, cv2.KMEANS_RANDOM_CENTERS)
            
            # Convertește la hex
            colors = []
            for center in centers:
                color_hex = "#{:02x}{:02x}{:02x}".format(int(center[2]), int(center[1]), int(center[0]))
                colors.append(color_hex)
            
            return colors[:3]  # Returnează primele 3 culori
        except:
            return ["#000000", "#FFFFFF", "#808080"]  # Fallback
    
    def _estimate_text_density(self, img):
        """Estimează densitatea textului în imagine"""
        try:
            # Convertește la grayscale
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Detectare margini pentru a estima textul
            edges = cv2.Canny(gray, 50, 150)
            
            # Calculează densitatea marginilor ca proxy pentru text
            edge_density = np.sum(edges > 0) / (edges.shape[0] * edges.shape[1])
            
            return float(edge_density)
        except:
            return 0.0
    
    async def process_video_async(self, video_data):
        """Procesează un video în mod asincron"""
        video_id, snippet = video_data
        
        try:
            # Verifică dacă există deja în baza de date
            with sqlite3.connect(self.config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM ads WHERE video_id = ?", (video_id,))
                if cursor.fetchone():
                    logger.info(f"Video {video_id} already processed, skipping.")
                    return
            
            # Descarcă și procesează
            await self._download_and_process(video_id, snippet)
            self.metrics.videos_processed += 1
            
        except Exception as e:
            logger.error(f"Failed to process video {video_id}: {e}")
            self.metrics.videos_failed += 1
            self.metrics.errors.append(f"{video_id}: {str(e)}")
    
    async def _download_and_process(self, video_id, snippet):
        """Descarcă și procesează un video"""
        output_file = f"{self.config.TEMP_DIR}/{video_id}.mp4"
        audio_file = f"{self.config.TEMP_DIR}/{video_id}.mp3"
        
        with temp_file_cleanup(output_file, audio_file):
            # Comandă yt-dlp pentru descărcare audio
            cmd = [
                "yt-dlp", 
                "-o", output_file,
                "-x", "--audio-format", "mp3",
                "--no-mtime", 
                "--retries", str(self.config.MAX_RETRIES),
                "--fragment-retries", str(self.config.MAX_RETRIES),
                f"https://www.youtube.com/watch?v={video_id}"
            ]
            
            # Execută descărcarea
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            try:
                stdout, stderr = await asyncio.wait_for(
                    process.communicate(), 
                    timeout=self.config.DOWNLOAD_TIMEOUT
                )
                
                if process.returncode != 0:
                    logger.error(f"yt-dlp failed for {video_id}: {stderr.decode()}")
                    return
                
            except asyncio.TimeoutError:
                process.kill()
                logger.error(f"Download timeout for {video_id}")
                return
            
            # Găsește fișierul audio descărcat
            audio_files = [f for f in os.listdir(self.config.TEMP_DIR) 
                          if f.startswith(video_id) and f.endswith('.mp3')]
            
            if not audio_files:
                logger.error(f"No audio file found for {video_id}")
                return
            
            actual_audio_file = os.path.join(self.config.TEMP_DIR, audio_files[0])
            
            # Analizează audio
            audio_features = self.analyze_audio_advanced(actual_audio_file)
            
            # Analizează thumbnail
            thumbnail_features = self.extract_thumbnail_features(video_id)
            
            # Obține statistici YouTube
            stats = await self._get_video_stats(video_id)
            
            # Salvează în baza de date
            await self._save_to_database(video_id, snippet, audio_features, thumbnail_features, stats)
    
    async def _get_video_stats(self, video_id):
        """Obține statisticile video de la YouTube"""
        for attempt in range(self.config.MAX_RETRIES):
            try:
                request = self.youtube.videos().list(part="statistics", id=video_id)
                response = request.execute()
                
                if response['items']:
                    stats = response['items'][0]['statistics']
                    return {
                        'views': int(stats.get('viewCount', 0)),
                        'likes': int(stats.get('likeCount', 0)),
                        'comments': int(stats.get('commentCount', 0))
                    }
                
            except HttpError as e:
                logger.warning(f"Stats fetch failed (attempt {attempt + 1}): {e}")
                await asyncio.sleep(2 ** attempt)
        
        return {'views': 0, 'likes': 0, 'comments': 0}
    
    async def _save_to_database(self, video_id, snippet, audio_features, thumbnail_features, stats):
        """Salvează datele în baza de date"""
        try:
            with sqlite3.connect(self.config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Calculează engagement rate
                engagement_rate = 0.0
                if stats['views'] > 0:
                    engagement_rate = (stats['likes'] + stats['comments']) / stats['views']
                
                # Inserează în tabela ads
                cursor.execute("""
                    INSERT INTO ads (
                        video_id, url, source, type, title, published_at, channel, 
                        description, views, likes, comments_count, engagement_rate, 
                        dominant_colors, duration, timestamp
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    video_id,
                    f"https://youtube.com/watch?v={video_id}",
                    "YouTube",
                    "video",
                    snippet['title'],
                    snippet.get('publishedAt', ''),
                    snippet['channelTitle'],
                    snippet.get('description', ''),
                    stats['views'],
                    stats['likes'],
                    stats['comments'],
                    engagement_rate,
                    json.dumps(thumbnail_features['dominant_colors'] if thumbnail_features else []),
                    int(audio_features['duration'] if audio_features else 0)
                ))
                
                ad_id = cursor.lastrowid
                
                # Inserează caracteristici audio
                if audio_features:
                    cursor.execute("""
                        INSERT INTO audio_features (
                            ad_id, tempo, energy, spectral_centroid, spectral_rolloff,
                            spectral_bandwidth, zero_crossing_rate, speech_ratio,
                            mfcc_features, chroma_features
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        ad_id,
                        audio_features['tempo'],
                        audio_features['energy'],
                        audio_features['spectral_centroid'],
                        audio_features['spectral_rolloff'],
                        audio_features['spectral_bandwidth'],
                        audio_features['zero_crossing_rate'],
                        audio_features['speech_ratio'],
                        json.dumps(audio_features['mfcc_mean']),
                        json.dumps(audio_features['chroma_mean'])
                    ))
                
                # Inserează caracteristici vizuale
                if thumbnail_features:
                    cursor.execute("""
                        INSERT OR IGNORE INTO visual_features (
                            ad_id, text_density, brightness, color_palette
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        ad_id,
                        thumbnail_features['text_density'],
                        thumbnail_features['brightness'],
                        json.dumps(thumbnail_features['dominant_colors'])
                    ))
                
                logger.info(f"Saved ad {ad_id} for video {video_id}")
                
        except Exception as e:
            logger.error(f"Database save failed for {video_id}: {e}")
    
    async def crawl_youtube_ads(self, query, max_results=None):
        """Funcția principală de crawling"""
        if max_results is None:
            max_results = self.config.MAX_RESULTS
        
        logger.info(f"Starting crawl with query: {query}")
        
        try:
            # Căutare videoclipuri
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                maxResults=min(50, max_results),  # YouTube API limit
                type="video",
                publishedAfter="2025-01-01T00:00:00Z",
                order="date"
            )
            
            all_videos = []
            videos_collected = 0
            
            while request and videos_collected < max_results:
                response = request.execute()
                
                for item in response['items']:
                    if videos_collected >= max_results:
                        break
                    
                    video_data = (item['id']['videoId'], item['snippet'])
                    all_videos.append(video_data)
                    videos_collected += 1
                
                # Următoarea pagină
                request = self.youtube.search().list_next(request, response)
                
                # Rate limiting
                await asyncio.sleep(60 / self.config.RATE_LIMIT_CALLS_PER_MINUTE)
            
            logger.info(f"Found {len(all_videos)} videos to process")
            
            # Procesează videoclipurile în paralel
            semaphore = asyncio.Semaphore(self.config.MAX_WORKERS)
            
            async def process_with_semaphore(video_data):
                async with semaphore:
                    await self.process_video_async(video_data)
            
            tasks = [process_with_semaphore(video) for video in all_videos]
            
            # Execută cu progress logging
            for i, task in enumerate(asyncio.as_completed(tasks)):
                await task
                if (i + 1) % 10 == 0:
                    self.metrics.log_progress()
            
            # Log final
            self.metrics.log_progress()
            logger.info("Crawling completed successfully")
            
        except Exception as e:
            logger.error(f"Crawling failed: {e}")
            raise

def init_database_advanced():
    """Inițializează baza de date cu tabele îmbunătățite"""
    with sqlite3.connect('/data/ads/ads_database.db') as conn:
        cursor = conn.cursor()
        
        # Tabela principală ads
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ads (
                id INTEGER PRIMARY KEY,
                video_id TEXT UNIQUE,
                url TEXT,
                source TEXT,
                type TEXT,
                title TEXT,
                published_at TEXT,
                channel TEXT,
                description TEXT,
                views INTEGER,
                likes INTEGER,
                comments_count INTEGER,
                engagement_rate REAL,
                dominant_colors TEXT,
                duration INTEGER,
                timestamp TEXT,
                processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Tabela pentru caracteristici audio îmbunătățite
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS audio_features (
                ad_id INTEGER PRIMARY KEY,
                tempo REAL,
                energy REAL,
                spectral_centroid REAL,
                spectral_rolloff REAL,
                spectral_bandwidth REAL,
                zero_crossing_rate REAL,
                speech_ratio REAL,
                mfcc_features TEXT,
                chroma_features TEXT,
                FOREIGN KEY (ad_id) REFERENCES ads(id)
            )
        """)
        
        # Tabela pentru caracteristici vizuale
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS visual_features (
                ad_id INTEGER PRIMARY KEY,
                text_density REAL,
                brightness REAL,
                color_palette TEXT,
                has_faces BOOLEAN DEFAULT 0,
                has_text BOOLEAN DEFAULT 0,
                FOREIGN KEY (ad_id) REFERENCES ads(id)
            )
        """)
        
        # Indexuri pentru performanță
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_id ON ads(video_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_published_at ON ads(published_at)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagement_rate ON ads(engagement_rate)")

async def main():
    """Funcția principală"""
    config = Config()
    
    # Inițializează baza de date
    init_database_advanced()
    
    # Creează crawler-ul
    crawler = YouTubeCrawler(config)
    
    # Queries pentru căutare
    queries = [
        "reclamă 2025 OR advertisement 2025 OR ad 2025 OR commercial 2025",
        "publicitate România 2025",
        "marketing campaign 2025"
    ]
    
    # Rulează crawling-ul pentru fiecare query
    for query in queries:
        try:
            await crawler.crawl_youtube_ads(query, max_results=100)
            logger.info(f"Completed crawling for query: {query}")
        except Exception as e:
            logger.error(f"Failed crawling for query '{query}': {e}")

if __name__ == "__main__":
    asyncio.run(main())
