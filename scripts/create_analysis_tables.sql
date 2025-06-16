-- Tabele pentru analiza comprehensivă 2025

-- Tabela pentru run-urile de analiză
CREATE TABLE IF NOT EXISTS analysis_runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    total_videos_found INTEGER DEFAULT 0,
    total_ads_detected INTEGER DEFAULT 0,
    total_errors INTEGER DEFAULT 0,
    api_calls_made INTEGER DEFAULT 0,
    processing_time REAL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela pentru categoriile de reclame
CREATE TABLE IF NOT EXISTS ad_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    category_name TEXT UNIQUE NOT NULL,
    description TEXT,
    keywords TEXT, -- JSON array cu keywords
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Tabela pentru brand detection
CREATE TABLE IF NOT EXISTS detected_brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    ad_id INTEGER,
    brand_name TEXT,
    confidence_score REAL,
    detection_method TEXT, -- 'title', 'description', 'visual', 'audio'
    FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE
);

-- Tabela pentru trending analysis
CREATE TABLE IF NOT EXISTS trending_analysis (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    analysis_date DATE,
    category TEXT,
    trend_score REAL,
    volume_change REAL, -- Procentual change in volume
    engagement_change REAL, -- Procentual change in engagement
    top_keywords TEXT, -- JSON array
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Inserează categoriile predefinite
INSERT OR IGNORE INTO ad_categories (category_name, description, keywords) VALUES 
('automotive', 'Car and vehicle advertisements', '["car", "auto", "vehicle", "driving", "mașină", "automobil"]'),
('technology', 'Technology and gadget advertisements', '["tech", "phone", "computer", "software", "app", "tehnologie"]'),
('food_beverage', 'Food and beverage advertisements', '["food", "drink", "restaurant", "mâncare", "băutură"]'),
('fashion', 'Fashion and clothing advertisements', '["fashion", "clothing", "style", "modă", "îmbrăcăminte"]'),
('beauty', 'Beauty and cosmetics advertisements', '["beauty", "cosmetics", "makeup", "frumusețe", "cosmetice"]'),
('finance', 'Financial services advertisements', '["bank", "finance", "money", "credit", "bancă", "finanțe"]'),
('travel', 'Travel and tourism advertisements', '["travel", "vacation", "hotel", "călătorie", "vacanță"]'),
('health', 'Health and medical advertisements', '["health", "medical", "doctor", "sănătate", "medical"]'),
('education', 'Education and learning advertisements', '["education", "learning", "course", "educație", "învățare"]'),
('entertainment', 'Entertainment advertisements', '["game", "movie", "music", "entertainment", "joc", "film"]');

-- Indexuri pentru performanță
CREATE INDEX IF NOT EXISTS idx_analysis_runs_date ON analysis_runs(start_date, end_date);
CREATE INDEX IF NOT EXISTS idx_detected_brands_ad_id ON detected_brands(ad_id);
CREATE INDEX IF NOT EXISTS idx_detected_brands_brand ON detected_brands(brand_name);
CREATE INDEX IF NOT EXISTS idx_trending_date ON trending_analysis(analysis_date);
CREATE INDEX IF NOT EXISTS idx_trending_category ON trending_analysis(category);

-- View pentru rapoarte comprehensive
CREATE VIEW IF NOT EXISTS comprehensive_ad_analysis AS
SELECT 
    a.*,
    af.tempo,
    af.energy,
    af.speech_ratio,
    vf.text_density,
    vf.brightness,
    ac.category_name,
    GROUP_CONCAT(db.brand_name) as detected_brands,
    AVG(db.confidence_score) as avg_brand_confidence
FROM ads a
LEFT JOIN audio_features af ON a.id = af.ad_id
LEFT JOIN visual_features vf ON a.id = vf.ad_id
LEFT JOIN ad_categories ac ON a.ad_type = ac.category_name
LEFT JOIN detected_brands db ON a.id = db.ad_id
WHERE a.published_at >= '2025-01-01'
GROUP BY a.id;

-- View pentru statistici pe categorii
CREATE VIEW IF NOT EXISTS category_statistics AS
SELECT 
    ad_type as category,
    COUNT(*) as total_ads,
    AVG(views) as avg_views,
    AVG(likes) as avg_likes,
    AVG(engagement_rate) as avg_engagement,
    AVG(confidence_score) as avg_confidence,
    MIN(published_at) as first_ad_date,
    MAX(published_at) as latest_ad_date
FROM ads 
WHERE published_at >= '2025-01-01'
GROUP BY ad_type
ORDER BY total_ads DESC;

-- View pentru trending brands
CREATE VIEW IF NOT EXISTS trending_brands AS
SELECT 
    db.brand_name,
    COUNT(*) as ad_count,
    AVG(a.views) as avg_views,
    AVG(a.engagement_rate) as avg_engagement,
    AVG(db.confidence_score) as avg_confidence,
    MAX(a.published_at) as latest_ad
FROM detected_brands db
JOIN ads a ON db.ad_id = a.id
WHERE a.published_at >= '2025-01-01'
GROUP BY db.brand_name
HAVING ad_count >= 3
ORDER BY ad_count DESC, avg_engagement DESC;

SELECT 'Analysis tables created successfully!' as message;
