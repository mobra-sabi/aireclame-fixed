#!/usr/bin/env python3
"""
REAL YouTube Crawler - folosește API-uri reale YouTube
Nu mai există date mock - totul este real
"""

import os
import sqlite3
import json
import time
import logging
import requests
from datetime import datetime, timedelta
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import threading
import signal
import sys

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/tmp/real_crawler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RealYouTubeCrawler:
    def __init__(self):
        self.running = False
        self.api_keys = self.load_api_keys()
        self.current_key_index = 0
        self.youtube = None
        self.db_path = '/data/ads/real_ads.db'
        self.stats = {
            'videos_checked': 0,
            'ads_found': 0,
            'api_calls': 0,
            'errors': 0,
            'start_time': None
        }
        
        # Creează directorul pentru DB
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        self.init_database()
        self.init_youtube_service()
        
        # Handler pentru oprire
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def load_api_keys(self):
        """Încarcă cheile API reale"""
        try:
            with open('api_keys.json', 'r') as f:
                keys = json.load(f)
                logger.info(f"Loaded {len(keys)} real YouTube API keys")
                return keys
        except Exception as e:
            logger.error(f"Failed to load API keys: {e}")
            return []
    
    def init_youtube_service(self):
        """Inițializează serviciul YouTube cu cheia curentă"""
        if not self.api_keys:
            logger.error("No API keys available!")
            return False
        
        try:
            key = self.api_keys[self.current_key_index]
            self.youtube = build('youtube', 'v3', developerKey=key)
            logger.info(f"YouTube service initialized with key #{self.current_key_index + 1}")
            return True
        except Exception as e:
            logger.error(f"Failed to initialize YouTube service: {e}")
            return False
    
    def rotate_api_key(self):
        """Rotește la următoarea cheie API"""
        if len(self.api_keys) > 1:
            self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
            logger.info(f"Rotating to API key #{self.current_key_index + 1}")
            return self.init_youtube_service()
        return False
    
    def init_database(self):
        """Creează baza de date reală"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Tabela pentru reclame reale
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS real_ads (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        video_id TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        channel_title TEXT NOT NULL,
                        channel_id TEXT NOT NULL,
                        published_at TEXT NOT NULL,
                        description TEXT,
                        thumbnail_url TEXT,
                        view_count INTEGER DEFAULT 0,
                        like_count INTEGER DEFAULT 0,
                        comment_count INTEGER DEFAULT 0,
                        duration_seconds INTEGER DEFAULT 0,
                        ad_confidence REAL DEFAULT 0.0,
                        ad_type TEXT,
                        detected_keywords TEXT,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Tabela pentru statistici
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS crawler_stats (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        videos_checked INTEGER,
                        ads_found INTEGER,
                        api_calls INTEGER,
                        errors INTEGER,
                        run_duration INTEGER,
                        timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                conn.commit()
                logger.info("Real database initialized")
                
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
    
    def search_youtube_videos(self, query, max_results=50):
        """Caută videoclipuri reale pe YouTube"""
        if not self.youtube:
            logger.error("YouTube service not initialized")
            return []
        
        try:
            # Caută videoclipuri din ultimele 7 zile
            published_after = (datetime.now() - timedelta(days=7)).isoformat() + 'Z'
            
            request = self.youtube.search().list(
                part="snippet",
                q=query,
                type="video",
                publishedAfter=published_after,
                maxResults=max_results,
                order="relevance"
            )
            
            response = request.execute()
            self.stats['api_calls'] += 1
            
            videos = []
            for item in response.get('items', []):
                videos.append({
                    'video_id': item['id']['videoId'],
                    'title': item['snippet']['title'],
                    'channel_title': item['snippet']['channelTitle'],
                    'channel_id': item['snippet']['channelId'],
                    'published_at': item['snippet']['publishedAt'],
                    'description': item['snippet'].get('description', ''),
                    'thumbnail_url': item['snippet']['thumbnails'].get('medium', {}).get('url', '')
                })
            
            logger.info(f"Found {len(videos)} real videos for query: {query}")
            return videos
            
        except HttpError as e:
            if e.resp.status == 403:
                logger.warning("API quota exceeded, rotating key...")
                if self.rotate_api_key():
                    return self.search_youtube_videos(query, max_results)
                else:
                    logger.error("All API keys exhausted!")
                    return []
            else:
                logger.error(f"YouTube API error: {e}")
                self.stats['errors'] += 1
                return []
        except Exception as e:
            logger.error(f"Search error: {e}")
            self.stats['errors'] += 1
            return []
    
    def get_video_details(self, video_id):
        """Obține detalii complete despre un video"""
        if not self.youtube:
            return None
        
        try:
            request = self.youtube.videos().list(
                part="statistics,contentDetails",
                id=video_id
            )
            
            response = request.execute()
            self.stats['api_calls'] += 1
            
            if response['items']:
                item = response['items'][0]
                stats = item.get('statistics', {})
                content = item.get('contentDetails', {})
                
                return {
                    'view_count': int(stats.get('viewCount', 0)),
                    'like_count': int(stats.get('likeCount', 0)),
                    'comment_count': int(stats.get('commentCount', 0)),
                    'duration': self.parse_duration(content.get('duration', 'PT0S'))
                }
        except Exception as e:
            logger.error(f"Error getting video details for {video_id}: {e}")
            self.stats['errors'] += 1
        
        return None
    
    def parse_duration(self, duration_str):
        """Parsează durata YouTube în secunde"""
        import re
        pattern = r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?'
        match = re.match(pattern, duration_str)
        if match:
            hours = int(match.group(1) or 0)
            minutes = int(match.group(2) or 0)
            seconds = int(match.group(3) or 0)
            return hours * 3600 + minutes * 60 + seconds
        return 0
    
    def detect_ad_content(self, video_data):
        """Detectează dacă un video este reclamă - algoritm real"""
        title = video_data['title'].lower()
        description = video_data['description'].lower()
        channel = video_data['channel_title'].lower()
        
        # Keywords reale pentru detectarea reclamelor
        ad_keywords = {
            'direct': ['advertisement', 'commercial', 'sponsored', 'ad', 'promo', 'promotion'],
            'romanian': ['publicitate', 'reclamă', 'reclama', 'promovare', 'sponsor'],
            'action': ['buy now', 'order now', 'limited time', 'special offer', 'discount'],
            'brand': ['official', 'new product', 'launch', 'campaign', 'brand new'],
            'sales': ['sale', 'offer', 'deal', 'price', 'cost', 'free shipping']
        }
        
        score = 0
        matched_keywords = []
        
        # Verifică în titlu (weight: 3)
        for category, keywords in ad_keywords.items():
            for keyword in keywords:
                if keyword in title:
                    score += 3
                    matched_keywords.append(f"title:{keyword}")
        
        # Verifică în descriere (weight: 2)
        for category, keywords in ad_keywords.items():
            for keyword in keywords:
                if keyword in description:
                    score += 2
                    matched_keywords.append(f"desc:{keyword}")
        
        # Verifică canalul (weight: 1)
        brand_indicators = ['official', 'brand', 'company', 'corp', 'inc', 'ltd', 'shop']
        for indicator in brand_indicators:
            if indicator in channel:
                score += 1
                matched_keywords.append(f"channel:{indicator}")
        
        # Calculează confidence real
        confidence = min(score / 15.0, 1.0)
        is_ad = score >= 4  # Threshold mai strict pentru acuratețe
        
        # Clasifică tipul reclamei
        ad_type = self.classify_ad_type(title + " " + description)
        
        return {
            'is_ad': is_ad,
            'confidence': confidence,
            'score': score,
            'matched_keywords': matched_keywords,
            'ad_type': ad_type
        }
    
    def classify_ad_type(self, text):
        """Clasifică tipul reclamei"""
        text = text.lower()
        
        categories = {
            'automotive': ['car', 'auto', 'vehicle', 'mașină', 'automobil', 'bmw', 'mercedes', 'audi', 'toyota'],
            'technology': ['tech', 'phone', 'computer', 'software', 'app', 'samsung', 'apple', 'google', 'microsoft'],
            'food_beverage': ['food', 'drink', 'restaurant', 'mâncare', 'băutură', 'coca cola', 'pepsi', 'mcdonalds'],
            'fashion': ['fashion', 'clothing', 'style', 'modă', 'nike', 'adidas', 'zara', 'h&m'],
            'beauty': ['beauty', 'cosmetics', 'makeup', 'frumusețe', 'loreal', 'maybelline', 'nivea'],
            'finance': ['bank', 'finance', 'money', 'credit', 'bancă', 'ing', 'bcr', 'raiffeisen'],
            'retail': ['shop', 'store', 'mall', 'magazin', 'emag', 'altex', 'dedeman', 'kaufland'],
            'entertainment': ['game', 'movie', 'music', 'netflix', 'hbo', 'disney', 'spotify']
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return 'other'
    
    def save_ad_to_database(self, video_data, ad_detection, video_details):
        """Salvează reclama reală în baza de date"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Verifică dacă există deja
                cursor.execute("SELECT id FROM real_ads WHERE video_id = ?", (video_data['video_id'],))
                if cursor.fetchone():
                    return False  # Există deja
                
                # Inserează reclama reală
                cursor.execute("""
                    INSERT INTO real_ads (
                        video_id, title, channel_title, channel_id, published_at,
                        description, thumbnail_url, view_count, like_count, comment_count,
                        duration_seconds, ad_confidence, ad_type, detected_keywords
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    video_data['video_id'],
                    video_data['title'],
                    video_data['channel_title'],
                    video_data['channel_id'],
                    video_data['published_at'],
                    video_data['description'][:1000],  # Limitează descrierea
                    video_data['thumbnail_url'],
                    video_details['view_count'] if video_details else 0,
                    video_details['like_count'] if video_details else 0,
                    video_details['comment_count'] if video_details else 0,
                    video_details['duration'] if video_details else 0,
                    ad_detection['confidence'],
                    ad_detection['ad_type'],
                    ','.join(ad_detection['matched_keywords'])
                ))
                
                conn.commit()
                self.stats['ads_found'] += 1
                logger.info(f"✅ Saved real ad: {video_data['title'][:50]}... (Confidence: {ad_detection['confidence']:.2f})")
                return True
                
        except Exception as e:
            logger.error(f"Error saving ad to database: {e}")
            self.stats['errors'] += 1
            return False
    
    def crawl_cycle(self):
        """Un ciclu complet de crawling REAL"""
        logger.info("🚀 Starting REAL crawl cycle...")
        
        # Queries reale pentru căutarea reclamelor
        search_queries = [
            "advertisement 2025",
            "commercial 2025", 
            "publicitate romania 2025",
            "reclamă nouă 2025",
            "sponsored content",
            "promo video 2025",
            "marketing campaign",
            "brand commercial",
            "product advertisement",
            "official commercial"
        ]
        
        cycle_start = time.time()
        cycle_videos = 0
        cycle_ads = 0
        
        for query in search_queries:
            if not self.running:
                break
                
            logger.info(f"🔍 Searching for: {query}")
            
            # Caută videoclipuri reale
            videos = self.search_youtube_videos(query, max_results=20)
            cycle_videos += len(videos)
            
            for video_data in videos:
                if not self.running:
                    break
                
                self.stats['videos_checked'] += 1
                
                # Detectează dacă este reclamă
                ad_detection = self.detect_ad_content(video_data)
                
                if ad_detection['is_ad']:
                    # Obține detalii complete
                    video_details = self.get_video_details(video_data['video_id'])
                    
                    # Salvează în baza de date
                    if self.save_ad_to_database(video_data, ad_detection, video_details):
                        cycle_ads += 1
                
                # Rate limiting pentru a nu depăși quota
                time.sleep(1)
            
            # Pauză între queries
            time.sleep(2)
        
        cycle_time = time.time() - cycle_start
        logger.info(f"✅ Cycle completed: {cycle_videos} videos checked, {cycle_ads} new ads found in {cycle_time:.1f}s")
        
        # Salvează statisticile
        self.save_stats()
    
    def save_stats(self):
        """Salvează statisticile reale"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                run_duration = int(time.time() - self.stats['start_time']) if self.stats['start_time'] else 0
                
                cursor.execute("""
                    INSERT INTO crawler_stats 
                    (videos_checked, ads_found, api_calls, errors, run_duration)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    self.stats['videos_checked'],
                    self.stats['ads_found'],
                    self.stats['api_calls'],
                    self.stats['errors'],
                    run_duration
                ))
                
                conn.commit()
                
        except Exception as e:
            logger.error(f"Error saving stats: {e}")
    
    def start_crawling(self):
        """Pornește crawling-ul continuu REAL"""
        self.running = True
        self.stats['start_time'] = time.time()
        
        logger.info("🎯 Starting REAL YouTube ad crawler...")
        logger.info(f"📊 Database: {self.db_path}")
        logger.info(f"🔑 API Keys: {len(self.api_keys)} available")
        
        # Salvează PID
        with open('/tmp/real_crawler.pid', 'w') as f:
            f.write(str(os.getpid()))
        
        try:
            while self.running:
                self.crawl_cycle()
                
                if self.running:
                    logger.info("⏳ Waiting 5 minutes before next cycle...")
                    for i in range(300):  # 5 minute = 300 secunde
                        if not self.running:
                            break
                        time.sleep(1)
                        
        except Exception as e:
            logger.error(f"Critical error: {e}")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Curăță la oprire"""
        self.running = False
        try:
            os.remove('/tmp/real_crawler.pid')
        except:
            pass
        logger.info("🛑 Crawler stopped")
    
    def signal_handler(self, signum, frame):
        """Handler pentru semnale de oprire"""
        logger.info(f"Received signal {signum}, stopping...")
        self.cleanup()
        sys.exit(0)
    
    def get_status(self):
        """Returnează statusul real"""
        return {
            'running': self.running,
            'stats': self.stats.copy(),
            'api_keys_count': len(self.api_keys),
            'current_key': self.current_key_index + 1,
            'database_path': self.db_path
        }

def main():
    """Funcția principală"""
    crawler = RealYouTubeCrawler()
    
    if not crawler.api_keys:
        logger.error("❌ No API keys found! Cannot start crawler.")
        return
    
    logger.info("🎯 Real YouTube Crawler initialized")
    status = crawler.get_status()
    logger.info(f"📊 Status: {status}")
    
    # Pornește crawling-ul
    crawler.start_crawling()

if __name__ == "__main__":
    main()
