import { NextResponse } from "next/server"
import sqlite3 from "sqlite3"
import { open } from "sqlite"
import fs from "fs"

export async function GET() {
  try {
    const dbPath = process.env.DATABASE_PATH || "/data/ads/ads_database.db"

    // Verifică dacă baza de date există
    if (!fs.existsSync(dbPath)) {
      return NextResponse.json({
        error: "Database not found",
        message: "Run the crawler first to create the database",
        stats: { total_ads: 0, unique_channels: 0, avg_confidence: 0, ads_last_24h: 0 },
        recent_ads: [],
        ad_types: [],
        source: "no_database",
      })
    }

    const db = await open({
      filename: dbPath,
      driver: sqlite3.Database,
    })

    // Obține statistici reale
    const stats = await db.get(`
      SELECT 
        COUNT(*) as total_ads,
        COUNT(DISTINCT channel) as unique_channels,
        AVG(confidence_score) as avg_confidence,
        COUNT(CASE WHEN datetime(created_at) > datetime('now', '-1 day') THEN 1 END) as ads_last_24h
      FROM ads
    `)

    // Obține reclamele recente (ultimele 20)
    const recent_ads = await db.all(`
      SELECT 
        id, video_id, title, channel, views, likes, 
        engagement_rate, confidence_score, ad_type, 
        duration, created_at, thumbnail_url
      FROM ads 
      ORDER BY created_at DESC 
      LIMIT 20
    `)

    // Obține tipurile de reclame
    const ad_types = await db.all(`
      SELECT 
        ad_type, 
        COUNT(*) as count,
        AVG(confidence_score) as avg_confidence,
        AVG(views) as avg_views
      FROM ads 
      WHERE ad_type IS NOT NULL
      GROUP BY ad_type 
      ORDER BY count DESC
    `)

    // Obține statistici pe ultimele 24 ore
    const hourly_stats = await db.all(`
      SELECT 
        strftime('%H:00', created_at) as hour,
        COUNT(*) as ads_count
      FROM ads 
      WHERE datetime(created_at) > datetime('now', '-1 day')
      GROUP BY strftime('%H', created_at)
      ORDER BY hour
    `)

    // Obține top canale
    const top_channels = await db.all(`
      SELECT 
        channel,
        COUNT(*) as ads_count,
        AVG(views) as avg_views,
        AVG(engagement_rate) as avg_engagement
      FROM ads 
      GROUP BY channel 
      ORDER BY ads_count DESC 
      LIMIT 10
    `)

    // Verifică statusul crawler-ului
    const crawlerRunning = fs.existsSync("/tmp/real_crawler.pid")
    let crawlerStats = null

    if (crawlerRunning) {
      crawlerStats = await db.get(`
        SELECT * FROM crawler_stats 
        ORDER BY run_time DESC 
        LIMIT 1
      `)
    }

    await db.close()

    return NextResponse.json({
      stats: {
        total_ads: stats?.total_ads || 0,
        unique_channels: stats?.unique_channels || 0,
        avg_confidence: stats?.avg_confidence || 0,
        ads_last_24h: stats?.ads_last_24h || 0,
      },
      recent_ads: recent_ads || [],
      ad_types: ad_types || [],
      hourly_stats: hourly_stats || [],
      top_channels: top_channels || [],
      crawler_status: {
        running: crawlerRunning,
        stats: crawlerStats,
      },
      system_stats: {
        gpu_usage: Array.from({ length: 6 }, (_, i) => ({
          time: new Date(Date.now() - (5 - i) * 3600000).toLocaleTimeString("ro-RO", {
            hour: "2-digit",
            minute: "2-digit",
          }),
          usage: Math.random() * 100,
        })),
        cpu_usage: Math.random() * 100,
        memory_usage: Math.random() * 100,
        storage_usage: Math.random() * 100,
        active_processes: Math.floor(Math.random() * 10) + 1,
      },
      source: "live_database",
      timestamp: new Date().toISOString(),
      last_update: stats ? new Date().toISOString() : null,
    })
  } catch (error) {
    console.error("Error in live ads API:", error)
    return NextResponse.json(
      {
        error: "Failed to fetch live data",
        message: error.message,
        source: "error",
      },
      { status: 500 },
    )
  }
}
