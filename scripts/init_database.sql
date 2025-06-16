-- Creează baza de date pentru sistemul de crawling reclame
-- Rulează acest script pentru a inițializa structura bazei de date

-- Tabela principală pentru reclame
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
    dominant_colors TEXT, -- JSON array cu culorile dominante
    duration INTEGER DEFAULT 0, -- în secunde
    timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela pentru caracteristici audio avansate
CREATE TABLE IF NOT EXISTS audio_features (
    ad_id INTEGER PRIMARY KEY,
    tempo REAL, -- BPM
    energy REAL, -- 0-1
    spectral_centroid REAL, -- Hz
    spectral_rolloff REAL, -- Hz
    spectral_bandwidth REAL, -- Hz
    zero_crossing_rate REAL, -- 0-1
    speech_ratio REAL, -- 0-1 (0=muzică, 1=vorbire)
    mfcc_features TEXT, -- JSON array cu MFCC features
    chroma_features TEXT, -- JSON array cu chroma features
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE
);

-- Tabela pentru caracteristici vizuale
CREATE TABLE IF NOT EXISTS visual_features (
    ad_id INTEGER PRIMARY KEY,
    text_density REAL DEFAULT 0.0, -- 0-1
    brightness REAL DEFAULT 0.0, -- 0-255
    color_palette TEXT, -- JSON array cu culorile dominante
    has_faces BOOLEAN DEFAULT 0,
    has_text BOOLEAN DEFAULT 0,
    face_count INTEGER DEFAULT 0,
    text_regions TEXT, -- JSON array cu regiunile de text
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE
);

-- Tabela pentru clasificarea reclamelor
CREATE TABLE IF NOT EXISTS ad_classifications (
    ad_id INTEGER PRIMARY KEY,
    category TEXT, -- ex: 'automotive', 'food', 'technology'
    subcategory TEXT,
    target_audience TEXT, -- ex: 'young_adults', 'families'
    emotional_tone TEXT, -- ex: 'happy', 'serious', 'exciting'
    confidence_score REAL DEFAULT 0.0, -- 0-1
    classified_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE
);

-- Tabela pentru metrici de performanță
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id INTEGER,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    measured_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE
);

-- Tabela pentru log-uri de procesare
CREATE TABLE IF NOT EXISTS processing_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    operation TEXT, -- 'download', 'audio_analysis', 'visual_analysis'
    status TEXT, -- 'success', 'error', 'warning'
    message TEXT,
    execution_time REAL, -- în secunde
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexuri pentru performanță
CREATE INDEX IF NOT EXISTS idx_ads_video_id ON ads(video_id);
CREATE INDEX IF NOT EXISTS idx_ads_published_at ON ads(published_at);
CREATE INDEX IF NOT EXISTS idx_ads_engagement_rate ON ads(engagement_rate);
CREATE INDEX IF NOT EXISTS idx_ads_views ON ads(views);
CREATE INDEX IF NOT EXISTS idx_ads_channel ON ads(channel);
CREATE INDEX IF NOT EXISTS idx_ads_source ON ads(source);

CREATE INDEX IF NOT EXISTS idx_audio_tempo ON audio_features(tempo);
CREATE INDEX IF NOT EXISTS idx_audio_energy ON audio_features(energy);
CREATE INDEX IF NOT EXISTS idx_audio_speech_ratio ON audio_features(speech_ratio);

CREATE INDEX IF NOT EXISTS idx_visual_brightness ON visual_features(brightness);
CREATE INDEX IF NOT EXISTS idx_visual_text_density ON visual_features(text_density);

CREATE INDEX IF NOT EXISTS idx_classifications_category ON ad_classifications(category);
CREATE INDEX IF NOT EXISTS idx_classifications_audience ON ad_classifications(target_audience);

CREATE INDEX IF NOT EXISTS idx_logs_status ON processing_logs(status);
CREATE INDEX IF NOT EXISTS idx_logs_operation ON processing_logs(operation);
CREATE INDEX IF NOT EXISTS idx_logs_created_at ON processing_logs(created_at);

-- Views pentru analize rapide
CREATE VIEW IF NOT EXISTS ads_with_features AS
SELECT 
    a.*,
    af.tempo,
    af.energy,
    af.spectral_centroid,
    af.speech_ratio,
    vf.text_density,
    vf.brightness,
    vf.has_faces,
    ac.category,
    ac.target_audience,
    ac.emotional_tone
FROM ads a
LEFT JOIN audio_features af ON a.id = af.ad_id
LEFT JOIN visual_features vf ON a.id = vf.ad_id
LEFT JOIN ad_classifications ac ON a.id = ac.ad_id;

-- View pentru statistici pe canal
CREATE VIEW IF NOT EXISTS channel_stats AS
SELECT 
    channel,
    COUNT(*) as total_ads,
    AVG(views) as avg_views,
    AVG(likes) as avg_likes,
    AVG(engagement_rate) as avg_engagement,
    MAX(views) as max_views,
    MIN(published_at) as first_ad,
    MAX(published_at) as latest_ad
FROM ads
WHERE channel IS NOT NULL
GROUP BY channel;

-- View pentru tendințe temporale
CREATE VIEW IF NOT EXISTS temporal_trends AS
SELECT 
    DATE(published_at) as date,
    COUNT(*) as ads_count,
    AVG(views) as avg_views,
    AVG(engagement_rate) as avg_engagement,
    AVG(af.tempo) as avg_tempo,
    AVG(af.energy) as avg_energy
FROM ads a
LEFT JOIN audio_features af ON a.id = af.ad_id
WHERE published_at IS NOT NULL
GROUP BY DATE(published_at)
ORDER BY date;

-- Inserează date de test (opțional)
INSERT OR IGNORE INTO ads (
    video_id, url, title, channel, views, likes, engagement_rate, published_at
) VALUES 
    ('test123', 'https://youtube.com/watch?v=test123', 'Test Ad 1', 'Test Channel', 1000, 50, 0.05, '2025-01-15'),
    ('test456', 'https://youtube.com/watch?v=test456', 'Test Ad 2', 'Another Channel', 5000, 200, 0.04, '2025-01-16');

-- Mesaj de confirmare
SELECT 'Database initialized successfully!' as message;
