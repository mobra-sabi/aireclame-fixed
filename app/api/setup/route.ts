import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const { dbPath } = await request.json()

    if (!dbPath) {
      return NextResponse.json({ error: "Database path is required" }, { status: 400 })
    }

    // Try to use filesystem operations
    try {
      const fs = await import("fs")
      const path = await import("path")

      // Ensure directory exists
      const dbDir = path.dirname(dbPath)
      if (!fs.existsSync(dbDir)) {
        try {
          fs.mkdirSync(dbDir, { recursive: true })
        } catch (error) {
          return NextResponse.json(
            {
              error: `Failed to create directory: ${error.message}`,
            },
            { status: 500 },
          )
        }
      }

      // Try to initialize database
      const sqlite3 = await import("sqlite3").catch(() => null)
      if (!sqlite3) {
        return NextResponse.json(
          {
            message: "SQLite not available in this environment. Using mock data instead.",
            path: dbPath,
            mode: "mock",
          },
          { status: 200 },
        )
      }

      const { open } = await import("sqlite")
      const db = await open({
        filename: dbPath,
        driver: sqlite3.default.Database,
      })

      // Create tables
      await db.exec(`
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
            dominant_colors TEXT,
            duration INTEGER DEFAULT 0,
            timestamp TEXT DEFAULT CURRENT_TIMESTAMP,
            processed_at DATETIME DEFAULT CURRENT_TIMESTAMP
        );

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
            FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE
        );

        CREATE TABLE IF NOT EXISTS visual_features (
            ad_id INTEGER PRIMARY KEY,
            text_density REAL DEFAULT 0.0,
            brightness REAL DEFAULT 0.0,
            color_palette TEXT,
            has_faces BOOLEAN DEFAULT 0,
            has_text BOOLEAN DEFAULT 0,
            FOREIGN KEY (ad_id) REFERENCES ads(id) ON DELETE CASCADE
        );

        CREATE INDEX IF NOT EXISTS idx_video_id ON ads(video_id);
        CREATE INDEX IF NOT EXISTS idx_published_at ON ads(published_at);
        CREATE INDEX IF NOT EXISTS idx_engagement_rate ON ads(engagement_rate);
      `)

      // Insert sample data
      await db.run(`
        INSERT OR IGNORE INTO ads (
            video_id, url, title, channel, views, likes, engagement_rate, published_at
        ) VALUES 
            ('sample1', 'https://youtube.com/watch?v=sample1', 'Reclamă Auto 2025 - Mașina Viitorului', 'AutoChannel', 15000, 750, 0.05, '2025-01-15T10:00:00Z'),
            ('sample2', 'https://youtube.com/watch?v=sample2', 'Publicitate Telefon Nou - Tehnologie Avansată', 'TechChannel', 25000, 1200, 0.048, '2025-01-16T14:30:00Z'),
            ('sample3', 'https://youtube.com/watch?v=sample3', 'Reclamă Băutură Răcoritoare - Vara 2025', 'DrinkChannel', 8000, 320, 0.04, '2025-01-17T16:45:00Z'),
            ('sample4', 'https://youtube.com/watch?v=sample4', 'Publicitate Magazin Online - Reduceri Speciale', 'ShopChannel', 12000, 480, 0.04, '2025-01-18T09:15:00Z'),
            ('sample5', 'https://youtube.com/watch?v=sample5', 'Reclamă Restaurant - Mâncare Delicioasă', 'FoodChannel', 18000, 900, 0.05, '2025-01-19T12:00:00Z')
      `)

      // Insert sample audio features
      await db.run(`
        INSERT OR IGNORE INTO audio_features (ad_id, tempo, energy, speech_ratio) VALUES 
            (1, 120, 0.8, 0.6),
            (2, 140, 0.9, 0.7),
            (3, 110, 0.7, 0.4),
            (4, 130, 0.6, 0.8),
            (5, 100, 0.5, 0.3)
      `)

      // Insert sample visual features
      await db.run(`
        INSERT OR IGNORE INTO visual_features (ad_id, text_density, brightness) VALUES 
            (1, 0.3, 180),
            (2, 0.4, 200),
            (3, 0.2, 220),
            (4, 0.5, 160),
            (5, 0.3, 190)
      `)

      await db.close()

      return NextResponse.json({
        message: "Database initialized successfully with sample data",
        path: dbPath,
        mode: "database",
      })
    } catch (fsError) {
      console.log("Filesystem operations failed:", fsError.message)
      return NextResponse.json(
        {
          message: "Database setup not available in this environment. Using mock data instead.",
          path: dbPath,
          mode: "mock",
          error: fsError.message,
        },
        { status: 200 },
      )
    }
  } catch (error) {
    console.error("Setup error:", error)
    return NextResponse.json(
      {
        message: "Using mock data mode due to setup limitations",
        mode: "mock",
        error: error.message,
      },
      { status: 200 },
    )
  }
}
