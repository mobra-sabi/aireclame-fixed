#!/usr/bin/env python3
"""
Crawler REAL pentru YouTube care colectează reclame în timp real
"""

import os
import sqlite3
import json
import time
import logging
import asyncio
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import requests
import threading
from dataclasses import dataclass
from typing import List, Dict, Any

# Configurare logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/real_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class CrawlerConfig:
    DATABASE_PATH: str = '/data/ads/ads_database.db'
    API_KEYS_FILE: str = 'api_keys.json'
    CRAWL_INTERVAL: int = 300  # 5 minute
    MAX_RESULTS_PER_SEARCH: int = 50
    RATE_LIMIT_DELAY: int = 2  # secunde între requests

class RealYouTubeCrawler:
    def __init__(self, config: CrawlerConfig):
        self.config = config
        self.running = False
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        self.youtube = None
        self.stats = {
            'total_videos_checked': 0,
            'total_ads_found': 0,
            'api_calls_made': 0,
            'errors': 0,
            'last_run': None
        }
        self._init_youtube_service()
        self._init_database()
    
    def _load_api_keys(self) -> List[str]:
        """Încarcă cheile API YouTube"""
        try:
            if os.path.exists(self.config.API_KEYS_FILE):
                with open(self.config.API_KEYS_FILE, 'r') as f:
                    keys = json.load(f)
                    logger.info(f"Loaded {len(keys)} API keys")
                    return keys
            else:
                logger.warning("No API keys file found, using demo mode")
                return []
        except Exception as e:
            logger.error(f"Error loading API keys: {e}")
            return []
    
    def _init_youtube_service(self):
        """Inițializează serviciul YouTube"""
        if not self.api_keys:
            logger.warning("No API keys available - running in demo mode")
            return
        
        try:
            key = self.api_keys[self.current_key_index]
            self.youtube = build('youtube', 'v3', developerKey=key)
            logger.info(f"YouTube service initialized with key {self.current_key_index}")
        except Exception as e:
            logger.error(f"Failed to initialize YouTube service: {e}")
    
    def _init_database(self):
        """Inițializează baza de date"""
        try:
            os.makedirs(os.path.dirname(self.config.DATABASE_PATH), exist_ok=True)
            
            with sqlite3.connect(self.config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # Creează tabela ads
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video_id TEXT UNIQUE NOT NULL,
                        url TEXT NOT NULL,
                        source TEXT DEFAULT 'YouTube',
                        type TEXT DEFAULT 'video',
                        title TEXT NOT NULL,
                        published_at TEXT,
                        channel TEXT,
                        description TEXT,
                        views INTEGER DEFAULT 0,
                        likes INTEGER DEFAULT 0,
                        comments_count INTEGER DEFAULT 0,
                        engagement_rate REAL DEFAULT 0.0,
                        confidence_score REAL DEFAULT 0.0,
                        ad_type TEXT,
                        duration INTEGER DEFAULT 0,
                        thumbnail_url TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                        updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Creează tabela pentru statistici crawler
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crawler_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        total_videos_checked INTEGER,
                        total_ads_found INTEGER,
                        api_calls_made INTEGER,
                        errors INTEGER,
                        run_time DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Indexuri pentru performanță
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_video_id ON ads(video_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON ads(created_at)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_ad_type ON ads(ad_type)")
                
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def _detect_ad_content(self, video_data: Dict) -> Dict[str, Any]:
        """Detectează dacă un video este reclamă"""
        snippet = video_data.get('snippet', {})
        title = snippet.get('title', '').lower()
        description = snippet.get('description', '').lower()
        channel_title = snippet.get('channelTitle', '').lower()
        
        # Keywords pentru detectarea reclamelor
        ad_keywords = [
            'advertisement', 'commercial', 'sponsored', 'promo', 'promotion',
            'ad', 'marketing', 'brand', 'product', 'sale', 'offer', 'deal',
            'publicitate', 'reclamă', 'reclama', 'promovare', 'ofertă',
            'reducere', 'discount', 'limited time', 'buy now', 'order now',
            'new product', 'launch', 'campaign', 'official'
        ]
        
        score = 0
        matched_keywords = []
        
        # Verifică title (weight: 3)
        for keyword in ad_keywords:
            if keyword in title:
                score += 3
                matched_keywords.append(f"title:{keyword}")
        
        # Verifică description (weight: 2)
        for keyword in ad_keywords:
            if keyword in description:
                score += 2
                matched_keywords.append(f"desc:{keyword}")
        
        # Verifică channel (weight: 1)
        brand_indicators = ['official', 'brand', 'company', 'corp', 'inc', 'ltd']
        for indicator in brand_indicators:
            if indicator in channel_title:
                score += 1
                matched_keywords.append(f"channel:{indicator}")
        
        # Calculează confidence
        confidence = min(score / 10.0, 1.0)
        is_ad = score >= 3
        
        return {
            'is_ad': is_ad,
            'confidence': confidence,
            'score': score,
            'matched_keywords': matched_keywords
        }
    
    def _classify_ad_type(self, snippet: Dict) -> str:
        """Clasifică tipul reclamei"""
        text = f"{snippet.get('title', '')} {snippet.get('description', '')}".lower()
        
        categories = {
            'automotive': ['car', 'auto', 'vehicle', 'driving', 'mașină', 'automobil', 'bmw', 'mercedes', 'audi'],
            'technology': ['tech', 'phone', 'computer', 'software', 'app', 'tehnologie', 'samsung', 'apple', 'google'],
            'food_beverage': ['food', 'drink', 'restaurant', 'mâncare', 'băutură', 'coca cola', 'pepsi', 'mcdonalds'],
            'fashion': ['fashion', 'clothing', 'style', 'modă', 'îmbrăcăminte', 'nike', 'adidas', 'zara'],
            'beauty': ['beauty', 'cosmetics', 'makeup', 'frumusețe', 'cosmetice', 'loreal', 'maybelline'],
            'finance': ['bank', 'finance', 'money', 'credit', 'bancă', 'finanțe', 'ing', 'bcr'],
            'retail': ['shop', 'store', 'mall', 'magazin', 'emag', 'altex', 'dedeman'],
            'entertainment': ['game', 'movie', 'music', 'entertainment', 'joc', 'film', 'netflix', 'hbo']
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return 'other'
    
    async def _get_video_statistics(self, video_id: str) -> Dict[str, Any]:
        """Obține statisticile unui video"""
        if not self.youtube:
            return {'views': 0, 'likes': 0, 'comments': 0, 'duration': 0}
        
        try:
            request = self.youtube.videos().list(
                part="statistics,contentDetails",
                id=video_id
            )
            response = request.execute()
            self.stats['api_calls_made'] += 1
            
            if response['items']:
                item = response['items'][0]
                stats = item.get('statistics', {})
                content_details = item.get('contentDetails', {})
                
                views = int(stats.get('viewCount', 0))
                likes = int(stats.get('likeCount', 0))
                comments = int(stats.get('commentCount', 0))
                
                # Calculează engagement rate
                engagement_rate = (likes + comments) / views if views > 0 else 0
                
                # Parsează durata
                duration_str = content_details.get('duration', 'PT0S')
                duration = self._parse_duration(duration_str)
                
                return {
                    'views': views,
                    'likes': likes,
                    'comments': comments,
                    'engagement_rate': engagement_rate,
                    'duration': duration
                }
        except Exception as e:
            logger.error(f"Error getting video statistics for {video_id}: {e}")
            self.stats['errors'] += 1
        
        return {'views': 0, 'likes': 0, 'comments': 0, 'engagement_rate': 0, 'duration': 0}
    
    def _parse_duration(self, duration_str: str) -> int:
        """Parsează durata YouTube în secunde"""
        try:
            # Format: PT1M30S sau PT30S sau PT1H2M30S
            import re
            pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
            match = re.match(pattern, duration_str)
            if match:
                hours = int(match.group(1) or 0)
                minutes = int(match.group(2) or 0)
                seconds = int(match.group(3) or 0)
                return hours * 3600 + minutes * 60 + seconds
        except:
            pass
        return 0
    
    async def _search_videos(self, query: str) -> List[Dict]:
        """Caută videoclipuri pe YouTube"""
        if not self.youtube:
            logger.warning("No YouTube service available")
            return []
        
        try:
            # Caută videoclipuri din ultimele 7 zile
            published_after = (datetime.now() - timedelta(days=7)).isoformat() + 'Z'
            
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                publishedAfter=published_after,
                maxResults=self.config.MAX_RESULTS_PER_SEARCH,
                order="date"
            )
            
            response = request.execute()
            self.stats['api_calls_made'] += 1
            
            videos = []
            for item in response.get('items', []):
                videos.append({
                    'video_id': item['id']['videoId'],
                    'snippet': item['snippet']
                })
            
            logger.info(f"Found {len(videos)} videos for query: {query}")
            return videos
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning("API quota exceeded, rotating key")
                self._rotate_api_key()
            else:
                logger.error(f"YouTube API error: {e}")
                self.stats['errors'] += 1
        except Exception as e:
            logger.error(f"Search error: {e}")
            self.stats['errors'] += 1
        
        return []
    
    def _rotate_api_key(self):
        """Rotește la următoarea cheie API"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            self._init_youtube_service()
            logger.info(f"Rotated to API key {self.current_key_index}")
    
    async def _save_ad_to_database(self, video_data: Dict, ad_detection: Dict, statistics: Dict):
        """Salvează reclama în baza de date"""
        try:
            with sqlite3.connect(self.config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                snippet = video_data['snippet']
                video_id = video_data['video_id']
                
                # Verifică dacă există deja
                cursor.execute("SELECT id FROM ads WHERE video_id = ?", (video_id,))
                if cursor.fetchone():
                    logger.debug(f"Video {video_id} already exists in database")
                    return
                
                # Inserează noua reclamă
                cursor.execute("""
                    INSERT INTO ads (
                        video_id, url, title, published_at, channel, description,
                        views, likes, comments_count, engagement_rate, confidence_score,
                        ad_type, duration, thumbnail_url
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_id,
                    f"https://youtube.com/watch?v={video_id}",
                    snippet['title'],
                    snippet.get('publishedAt', ''),
                    snippet['channelTitle'],
                    snippet.get('description', '')[:500],  # Limitează descrierea
                    statistics['views'],
                    statistics['likes'],
                    statistics['comments'],
                    statistics['engagement_rate'],
                    ad_detection['confidence'],
                    self._classify_ad_type(snippet),
                    statistics['duration'],
                    snippet.get('thumbnails', {}).get('medium', {}).get('url', '')
                ))
                
                self.stats['total_ads_found'] += 1
                logger.info(f"Saved new ad: {snippet['title'][:50]}...")
                
        except Exception as e:
            logger.error(f"Error saving ad to database: {e}")
            self.stats['errors'] += 1
    
    async def _crawl_cycle(self):
        """Un ciclu complet de crawling"""
        logger.info("Starting crawl cycle...")
        
        # Queries pentru căutare
        search_queries = [
            "advertisement 2025",
            "commercial 2025",
            "publicitate 2025",
            "reclamă 2025",
            "promo 2025",
            "sponsored content",
            "marketing campaign",
            "brand advertisement",
            "product launch 2025",
            "new product commercial"
        ]
        
        cycle_start = time.time()
        videos_in_cycle = 0
        ads_in_cycle = 0
        
        for query in search_queries:
            try:
                # Caută videoclipuri
                videos = await self._search_videos(query)
                videos_in_cycle += len(videos)
                
                for video_data in videos:
                    self.stats['total_videos_checked'] += 1
                    
                    # Detectează dacă este reclamă
                    ad_detection = self._detect_ad_content(video_data)
                    
                    if ad_detection['is_ad']:
                        # Obține statistici detaliate
                        statistics = await self._get_video_statistics(video_data['video_id'])
                        
                        # Salvează în baza de date
                        await self._save_ad_to_database(video_data, ad_detection, statistics)
                        ads_in_cycle += 1
                    
                    # Rate limiting
                    await asyncio.sleep(self.config.RATE_LIMIT_DELAY)
                
                # Pauză între queries
                await asyncio.sleep(5)
                
            except Exception as e:
                logger.error(f"Error processing query '{query}': {e}")
                self.stats['errors'] += 1
        
        cycle_time = time.time() - cycle_start
        logger.info(f"Crawl cycle completed: {videos_in_cycle} videos checked, "
                   f"{ads_in_cycle} ads found in {cycle_time:.1f}s")
        
        # Salvează statisticile
        self._save_crawler_stats()
    
    def _save_crawler_stats(self):
        """Salvează statisticile crawler-ului"""
        try:
            with sqlite3.connect(self.config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO crawler_stats 
                    (total_videos_checked, total_ads_found, api_calls_made, errors)
                    VALUES (?, ?, ?, ?)
                """, (
                    self.stats['total_videos_checked'],
                    self.stats['total_ads_found'],
                    self.stats['api_calls_made'],
                    self.stats['errors']
                ))
                self.stats['last_run'] = datetime.now().isoformat()
        except Exception as e:
            logger.error(f"Error saving crawler stats: {e}")
    
    def get_status(self) -> Dict[str, Any]:
        """Returnează statusul crawler-ului"""
        return {
            'running': self.running,
            'stats': self.stats.copy(),
            'has_api_keys': len(self.api_keys) > 0,
            'current_api_key_index': self.current_key_index,
            'database_path': self.config.DATABASE_PATH
        }
    
    async def start_continuous_crawling(self):
        """Pornește crawling-ul continuu"""
        self.running = True
        logger.info("Starting continuous YouTube crawling...")
        
        # Salvează PID pentru control
        with open('/tmp/real_crawler.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            while self.running:
                await self._crawl_cycle()
                
                if self.running:  # Verifică din nou după ciclu
                    logger.info(f"Waiting {self.config.CRAWL_INTERVAL} seconds before next cycle...")
                    await asyncio.sleep(self.config.CRAWL_INTERVAL)
                    
        except KeyboardInterrupt:
            logger.info("Received interrupt signal")
        except Exception as e:
            logger.error(f"Critical error in crawling loop: {e}")
        finally:
            self.running = False
            try:
                os.remove('/tmp/real_crawler.pid')
            except:
                pass
            logger.info("Crawler stopped")
    
    def stop(self):
        """Oprește crawler-ul"""
        self.running = False

async def main():
    """Funcția principală"""
    config = CrawlerConfig()
    crawler = RealYouTubeCrawler(config)
    
    # Afișează statusul inițial
    status = crawler.get_status()
    logger.info(f"Crawler status: {status}")
    
    if not status['has_api_keys']:
        logger.warning("No YouTube API keys found. Create api_keys.json with your keys.")
        logger.info("Running in demo mode - will create sample data...")
        
        # Creează date demo pentru testare
        await crawler._create_demo_data()
    
    # Pornește crawling-ul
    await crawler.start_continuous_crawling()

if __name__ == "__main__":
    asyncio.run(main())
