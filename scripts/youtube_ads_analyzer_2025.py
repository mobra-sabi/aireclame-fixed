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
from datetime import datetime, timedelta
import cv2
from PIL import Image
import requests
from typing import List, Dict, Any
import re

# Configurare logging îmbunătățită
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('youtube_ads_2025_analysis.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class AnalysisConfig:
    MAX_RESULTS_PER_QUERY: int = 500
    AUDIO_DURATION: int = 30
    DOWNLOAD_TIMEOUT: int = 120
    MAX_RETRIES: int = 5
    DATABASE_PATH: str = '/data/ads/ads_database.db'
    TEMP_DIR: str = '/tmp'
    MAX_WORKERS: int = 8
    RATE_LIMIT_CALLS_PER_MINUTE: int = 90
    ANALYSIS_START_DATE: str = '2025-01-01T00:00:00Z'
    ANALYSIS_END_DATE: str = '2025-12-31T23:59:59Z'

class YouTube2025Analyzer:
    def __init__(self, config: AnalysisConfig):
        self.config = config
        self.api_keys = self._load_api_keys()
        self.current_key_index = 0
        self.youtube = self._get_youtube_service()
        self.processed_videos = set()
        self.analysis_stats = {
            'total_videos_found': 0,
            'total_ads_detected': 0,
            'total_errors': 0,
            'api_calls_made': 0,
            'processing_time': 0
        }
        
    def _load_api_keys(self) -> List[str]:
        """Încarcă cheile API YouTube"""
        try:
            with open('api_keys.json', 'r') as f:
                keys = json.load(f)
                logger.info(f"Loaded {len(keys)} YouTube API keys")
                return keys
        except FileNotFoundError:
            logger.error("api_keys.json not found")
            return []
    
    def _get_youtube_service(self):
        """Obține serviciul YouTube cu rotația cheilor API"""
        for attempt in range(len(self.api_keys)):
            try:
                key = self.api_keys[self.current_key_index]
                service = build('youtube', 'v3', developerKey=key)
                logger.info(f"Using API key index {self.current_key_index}")
                return service
            except HttpError as e:
                logger.warning(f"API key {self.current_key_index} failed: {e}")
                self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
                continue
        raise Exception("No valid API keys available")
    
    def _rotate_api_key(self):
        """Rotește la următoarea cheie API"""
        self.current_key_index = (self.current_key_index + 1) % len(self.api_keys)
        self.youtube = self._get_youtube_service()
        logger.info(f"Rotated to API key index {self.current_key_index}")
    
    def get_comprehensive_search_queries(self) -> List[Dict[str, Any]]:
        """Generează queries comprehensive pentru detectarea reclamelor din 2025"""
        
        # Queries de bază pentru reclame
        base_ad_queries = [
            "advertisement 2025",
            "commercial 2025", 
            "ad 2025",
            "promo 2025",
            "sponsored 2025",
            "marketing 2025",
            "publicitate 2025",
            "reclamă 2025",
            "reclama 2025"
        ]
        
        # Categorii de produse/servicii
        product_categories = [
            "automotive car advertisement 2025",
            "technology tech ad 2025", 
            "food beverage commercial 2025",
            "fashion clothing ad 2025",
            "beauty cosmetics advertisement 2025",
            "finance banking commercial 2025",
            "travel tourism ad 2025",
            "health medical advertisement 2025",
            "education learning ad 2025",
            "entertainment gaming commercial 2025",
            "real estate property ad 2025",
            "retail shopping advertisement 2025"
        ]
        
        # Branduri mari care fac reclame
        major_brands = [
            "coca cola advertisement 2025",
            "pepsi commercial 2025",
            "nike ad 2025",
            "adidas commercial 2025",
            "apple advertisement 2025",
            "samsung ad 2025",
            "google commercial 2025",
            "microsoft advertisement 2025",
            "amazon ad 2025",
            "netflix commercial 2025"
        ]
        
        # Queries pentru piețe specifice
        regional_queries = [
            "romania advertisement 2025",
            "romanian commercial 2025",
            "bucuresti ad 2025",
            "cluj advertisement 2025",
            "timisoara commercial 2025"
        ]
        
        # Combină toate queries
        all_queries = []
        
        for query in base_ad_queries + product_categories + major_brands + regional_queries:
            all_queries.append({
                'q': query,
                'order': 'date',
                'type': 'video',
                'publishedAfter': self.config.ANALYSIS_START_DATE,
                'publishedBefore': self.config.ANALYSIS_END_DATE,
                'maxResults': 50
            })
        
        # Adaugă queries pentru canale specifice de advertising
        advertising_channels = [
            "UCrAav-QgGtjdVEmr9DtM3rQ",  # Exemplu canal advertising
            "UCYfdidRxbB8Qhf0Nx7ioOYw"   # Exemplu canal marketing
        ]
        
        for channel_id in advertising_channels:
            all_queries.append({
                'channelId': channel_id,
                'order': 'date',
                'type': 'video',
                'publishedAfter': self.config.ANALYSIS_START_DATE,
                'publishedBefore': self.config.ANALYSIS_END_DATE,
                'maxResults': 50
            })
        
        logger.info(f"Generated {len(all_queries)} search queries for 2025 analysis")
        return all_queries
    
    async def search_videos_comprehensive(self) -> List[Dict[str, Any]]:
        """Căutare comprehensivă a videoclipurilor din 2025"""
        all_videos = []
        queries = self.get_comprehensive_search_queries()
        
        for i, query_params in enumerate(queries):
            try:
                logger.info(f"Processing query {i+1}/{len(queries)}: {query_params.get('q', 'Channel search')}")
                
                # Rate limiting
                await asyncio.sleep(60 / self.config.RATE_LIMIT_CALLS_PER_MINUTE)
                
                videos = await self._search_with_pagination(query_params)
                all_videos.extend(videos)
                
                self.analysis_stats['api_calls_made'] += 1
                
                logger.info(f"Found {len(videos)} videos for this query. Total so far: {len(all_videos)}")
                
            except HttpError as e:
                if e.resp.status == 403:  # Quota exceeded
                    logger.warning("API quota exceeded, rotating key")
                    self._rotate_api_key()
                    await asyncio.sleep(5)
                    continue
                else:
                    logger.error(f"Error in search query {i}: {e}")
                    continue
            except Exception as e:
                logger.error(f"Unexpected error in query {i}: {e}")
                continue
        
        # Remove duplicates based on video_id
        unique_videos = {}
        for video in all_videos:
            video_id = video['id']['videoId'] if 'id' in video else video.get('videoId')
            if video_id and video_id not in unique_videos:
                unique_videos[video_id] = video
        
        final_videos = list(unique_videos.values())
        self.analysis_stats['total_videos_found'] = len(final_videos)
        
        logger.info(f"Total unique videos found: {len(final_videos)}")
        return final_videos
    
    async def _search_with_pagination(self, query_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Căutare cu paginare pentru a obține toate rezultatele"""
        all_videos = []
        next_page_token = None
        max_pages = 10  # Limitează la 10 pagini per query
        
        for page in range(max_pages):
            try:
                search_params = query_params.copy()
                if next_page_token:
                    search_params['pageToken'] = next_page_token
                
                request = self.youtube.search().list(
                    part="snippet",
                    **search_params
                )
                
                response = request.execute()
                
                if 'items' in response:
                    all_videos.extend(response['items'])
                
                next_page_token = response.get('nextPageToken')
                if not next_page_token:
                    break
                    
                # Rate limiting between pages
                await asyncio.sleep(1)
                
            except Exception as e:
                logger.error(f"Error in pagination page {page}: {e}")
                break
        
        return all_videos
    
    def detect_ad_content(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Detectează dacă un video este reclamă folosind multiple criterii"""
        snippet = video_data.get('snippet', {})
        title = snippet.get('title', '').lower()
        description = snippet.get('description', '').lower()
        channel_title = snippet.get('channelTitle', '').lower()
        
        ad_indicators = {
            'title_keywords': 0,
            'description_keywords': 0,
            'channel_indicators': 0,
            'duration_indicator': 0,
            'total_score': 0
        }
        
        # Keywords care indică reclame
        ad_keywords = [
            'advertisement', 'commercial', 'sponsored', 'promo', 'promotion',
            'ad', 'marketing', 'brand', 'product', 'sale', 'offer', 'deal',
            'publicitate', 'reclamă', 'reclama', 'promovare', 'ofertă',
            'reducere', 'discount', 'limited time', 'buy now', 'order now'
        ]
        
        # Verifică title
        for keyword in ad_keywords:
            if keyword in title:
                ad_indicators['title_keywords'] += 1
        
        # Verifică description
        for keyword in ad_keywords:
            if keyword in description:
                ad_indicators['description_keywords'] += 1
        
        # Verifică channel indicators
        brand_indicators = ['official', 'brand', 'company', 'corp', 'inc', 'ltd']
        for indicator in brand_indicators:
            if indicator in channel_title:
                ad_indicators['channel_indicators'] += 1
        
        # Calculează scorul total
        ad_indicators['total_score'] = (
            ad_indicators['title_keywords'] * 3 +
            ad_indicators['description_keywords'] * 2 +
            ad_indicators['channel_indicators'] * 1
        )
        
        # Determină dacă este reclamă (threshold = 3)
        is_ad = ad_indicators['total_score'] >= 3
        confidence = min(ad_indicators['total_score'] / 10, 1.0)
        
        return {
            'is_ad': is_ad,
            'confidence': confidence,
            'indicators': ad_indicators,
            'reasoning': f"Score: {ad_indicators['total_score']}, Title keywords: {ad_indicators['title_keywords']}, Desc keywords: {ad_indicators['description_keywords']}"
        }
    
    async def analyze_video_comprehensive(self, video_data: Dict[str, Any]) -> Dict[str, Any]:
        """Analiză comprehensivă a unui video"""
        video_id = video_data['id']['videoId'] if 'id' in video_data else video_data.get('videoId')
        snippet = video_data.get('snippet', {})
        
        try:
            # Detectează dacă este reclamă
            ad_detection = self.detect_ad_content(video_data)
            
            if not ad_detection['is_ad']:
                logger.debug(f"Video {video_id} not detected as ad, skipping detailed analysis")
                return None
            
            # Obține statistici video
            stats = await self._get_video_statistics(video_id)
            
            # Analiză audio (dacă este detectată ca reclamă)
            audio_features = None
            if ad_detection['confidence'] > 0.7:
                try:
                    audio_features = await self._analyze_audio_features(video_id)
                except Exception as e:
                    logger.warning(f"Audio analysis failed for {video_id}: {e}")
            
            # Analiză thumbnail
            thumbnail_features = self._analyze_thumbnail(video_id)
            
            # Clasificare categorii
            category = self._classify_ad_category(snippet)
            
            analysis_result = {
                'video_id': video_id,
                'title': snippet.get('title', ''),
                'channel': snippet.get('channelTitle', ''),
                'published_at': snippet.get('publishedAt', ''),
                'description': snippet.get('description', '')[:500],  # Limitează descrierea
                'ad_detection': ad_detection,
                'statistics': stats,
                'audio_features': audio_features,
                'thumbnail_features': thumbnail_features,
                'category': category,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            self.analysis_stats['total_ads_detected'] += 1
            return analysis_result
            
        except Exception as e:
            logger.error(f"Error analyzing video {video_id}: {e}")
            self.analysis_stats['total_errors'] += 1
            return None
    
    async def _get_video_statistics(self, video_id: str) -> Dict[str, Any]:
        """Obține statisticile unui video"""
        try:
            request = self.youtube.videos().list(
                part="statistics,contentDetails",
                id=video_id
            )
            response = request.execute()
            
            if response['items']:
                item = response['items'][0]
                stats = item.get('statistics', {})
                content_details = item.get('contentDetails', {})
                
                return {
                    'views': int(stats.get('viewCount', 0)),
                    'likes': int(stats.get('likeCount', 0)),
                    'comments': int(stats.get('commentCount', 0)),
                    'duration': content_details.get('duration', ''),
                    'engagement_rate': self._calculate_engagement_rate(stats)
                }
        except Exception as e:
            logger.warning(f"Failed to get statistics for {video_id}: {e}")
        
        return {'views': 0, 'likes': 0, 'comments': 0, 'duration': '', 'engagement_rate': 0}
    
    def _calculate_engagement_rate(self, stats: Dict[str, Any]) -> float:
        """Calculează rata de engagement"""
        views = int(stats.get('viewCount', 0))
        likes = int(stats.get('likeCount', 0))
        comments = int(stats.get('commentCount', 0))
        
        if views > 0:
            return (likes + comments) / views
        return 0
    
    def _classify_ad_category(self, snippet: Dict[str, Any]) -> str:
        """Clasifică categoria reclamei"""
        title = snippet.get('title', '').lower()
        description = snippet.get('description', '').lower()
        text = f"{title} {description}"
        
        categories = {
            'automotive': ['car', 'auto', 'vehicle', 'driving', 'mașină', 'automobil'],
            'technology': ['tech', 'phone', 'computer', 'software', 'app', 'tehnologie'],
            'food_beverage': ['food', 'drink', 'restaurant', 'mâncare', 'băutură'],
            'fashion': ['fashion', 'clothing', 'style', 'modă', 'îmbrăcăminte'],
            'beauty': ['beauty', 'cosmetics', 'makeup', 'frumusețe', 'cosmetice'],
            'finance': ['bank', 'finance', 'money', 'credit', 'bancă', 'finanțe'],
            'travel': ['travel', 'vacation', 'hotel', 'călătorie', 'vacanță'],
            'health': ['health', 'medical', 'doctor', 'sănătate', 'medical'],
            'education': ['education', 'learning', 'course', 'educație', 'învățare'],
            'entertainment': ['game', 'movie', 'music', 'entertainment', 'joc', 'film']
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in text:
                    return category
        
        return 'other'
    
    async def save_analysis_results(self, results: List[Dict[str, Any]]):
        """Salvează rezultatele analizei în baza de date"""
        try:
            with sqlite3.connect(self.config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                for result in results:
                    if not result:
                        continue
                    
                    # Inserează în tabela ads
                    cursor.execute("""
                        INSERT OR REPLACE INTO ads (
                            video_id, url, source, type, title, published_at, channel,
                            description, views, likes, comments_count, engagement_rate,
                            confidence_score, ad_type, duration, timestamp
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                    """, (
                        result['video_id'],
                        f"https://youtube.com/watch?v={result['video_id']}",
                        "YouTube",
                        "advertisement",
                        result['title'],
                        result['published_at'],
                        result['channel'],
                        result['description'],
                        result['statistics']['views'],
                        result['statistics']['likes'],
                        result['statistics']['comments'],
                        result['statistics']['engagement_rate'],
                        result['ad_detection']['confidence'],
                        result['category'],
                        result['statistics']['duration'],
                    ))
                    
                    ad_id = cursor.lastrowid
                    
                    # Inserează audio features dacă există
                    if result['audio_features']:
                        cursor.execute("""
                            INSERT OR REPLACE INTO audio_features (
                                ad_id, tempo, energy, spectral_centroid,
                                speech_ratio, analysis_data
                            ) VALUES (?, ?, ?, ?, ?, ?)
                        """, (
                            ad_id,
                            result['audio_features'].get('tempo', 0),
                            result['audio_features'].get('energy', 0),
                            result['audio_features'].get('spectral_centroid', 0),
                            result['audio_features'].get('speech_ratio', 0),
                            json.dumps(result['audio_features'])
                        ))
                
                logger.info(f"Saved {len(results)} analysis results to database")
                
        except Exception as e:
            logger.error(f"Error saving results to database: {e}")
    
    async def run_comprehensive_analysis(self):
        """Rulează analiza comprehensivă pentru toate reclamele din 2025"""
        start_time = datetime.now()
        logger.info("Starting comprehensive 2025 YouTube ads analysis")
        
        try:
            # Căutare comprehensivă
            logger.info("Phase 1: Comprehensive video search")
            all_videos = await self.search_videos_comprehensive()
            
            # Analiză în batch-uri
            logger.info("Phase 2: Detailed video analysis")
            batch_size = 50
            all_results = []
            
            for i in range(0, len(all_videos), batch_size):
                batch = all_videos[i:i + batch_size]
                logger.info(f"Processing batch {i//batch_size + 1}/{(len(all_videos) + batch_size - 1)//batch_size}")
                
                # Procesează batch-ul în paralel
                tasks = [self.analyze_video_comprehensive(video) for video in batch]
                batch_results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filtrează rezultatele valide
                valid_results = [r for r in batch_results if r and not isinstance(r, Exception)]
                all_results.extend(valid_results)
                
                # Salvează rezultatele batch-ului
                if valid_results:
                    await self.save_analysis_results(valid_results)
                
                # Rate limiting între batch-uri
                await asyncio.sleep(2)
            
            # Statistici finale
            end_time = datetime.now()
            self.analysis_stats['processing_time'] = (end_time - start_time).total_seconds()
            
            logger.info("=== ANALYSIS COMPLETE ===")
            logger.info(f"Total videos found: {self.analysis_stats['total_videos_found']}")
            logger.info(f"Total ads detected: {self.analysis_stats['total_ads_detected']}")
            logger.info(f"Total errors: {self.analysis_stats['total_errors']}")
            logger.info(f"API calls made: {self.analysis_stats['api_calls_made']}")
            logger.info(f"Processing time: {self.analysis_stats['processing_time']:.2f} seconds")
            
            # Salvează statisticile
            await self._save_analysis_statistics()
            
        except Exception as e:
            logger.error(f"Critical error in comprehensive analysis: {e}")
            raise
    
    async def _save_analysis_statistics(self):
        """Salvează statisticile analizei"""
        try:
            with sqlite3.connect(self.config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO analysis_runs (
                        start_date, end_date, total_videos_found, total_ads_detected,
                        total_errors, api_calls_made, processing_time, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """, (
                    self.config.ANALYSIS_START_DATE,
                    self.config.ANALYSIS_END_DATE,
                    self.analysis_stats['total_videos_found'],
                    self.analysis_stats['total_ads_detected'],
                    self.analysis_stats['total_errors'],
                    self.analysis_stats['api_calls_made'],
                    self.analysis_stats['processing_time']
                ))
                
                logger.info("Analysis statistics saved to database")
                
        except Exception as e:
            logger.error(f"Error saving analysis statistics: {e}")

async def main():
    """Funcția principală pentru analiza 2025"""
    config = AnalysisConfig()
    
    # Verifică dacă există cheile API
    if not os.path.exists('api_keys.json'):
        logger.error("api_keys.json not found. Please create it with your YouTube API keys.")
        return
    
    # Inițializează analizorul
    analyzer = YouTube2025Analyzer(config)
    
    # Rulează analiza comprehensivă
    await analyzer.run_comprehensive_analysis()

if __name__ == "__main__":
    asyncio.run(main())
