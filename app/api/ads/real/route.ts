import { NextResponse } from "next/server"
import sqlite3 from "sqlite3"
import { open } from "sqlite"
import fs from "fs"

export async function GET() {
  try {
    const dbPath = "/data/ads/real_ads.db"

    // Verifică dacă baza de date există
    if (!fs.existsSync(dbPath)) {
      return NextResponse.json({
        error: "Real database not found",
        message: "Start the real crawler first: ./scripts/start_real_crawler.sh start",
        stats: { total_ads: 0, unique_channels: 0, avg_confidence: 0, ads_last_24h: 0 },
        recent_ads: [],
        ad_types: [],
        source: "no_real_database",
      })
    }

    const db = await open({
      filename: dbPath,
      driver: sqlite3.Database,
    })

    // Statistici reale din baza de date
    const stats = await db.get(`
      SELECT 
        COUNT(*) as total_ads,
        COUNT(DISTINCT channel_title) as unique_channels,
        AVG(ad_confidence) as avg_confidence,
        COUNT(CASE WHEN datetime(created_at) > datetime('now', '-1 day') THEN 1 END) as ads_last_24h
      FROM real_ads
    `)

    // Reclamele reale recente
    const recent_ads = await db.all(`
      SELECT 
        id, video_id, title, channel_title as channel, view_count as views, 
        like_count as likes, comment_count, duration_seconds as duration,
        ad_confidence as confidence_score, ad_type, created_at, thumbnail_url
      FROM real_ads 
      ORDER BY created_at DESC 
      LIMIT 20
    `)

    // Tipurile reale de reclame
    const ad_types = await db.all(`
      SELECT 
        ad_type, 
        COUNT(*) as count,
        AVG(ad_confidence) as avg_confidence,
        AVG(view_count) as avg_views
      FROM real_ads 
      WHERE ad_type IS NOT NULL AND ad_type != ''
      GROUP BY ad_type 
      ORDER BY count DESC
    `)

    // Statistici pe ore (ultimele 24h)
    const hourly_stats = await db.all(`
      SELECT 
        strftime('%H:00', created_at) as hour,
        COUNT(*) as ads_count
      FROM real_ads 
      WHERE datetime(created_at) > datetime('now', '-1 day')
      GROUP BY strftime('%H', created_at)
      ORDER BY hour
    `)

    // Top canale reale
    const top_channels = await db.all(`
      SELECT 
        channel_title as channel,
        COUNT(*) as ads_count,
        AVG(view_count) as avg_views,
        AVG(ad_confidence) as avg_confidence
      FROM real_ads 
      GROUP BY channel_title 
      ORDER BY ads_count DESC 
      LIMIT 10
    `)

    // Verifică dacă crawler-ul rulează
    const crawlerRunning = fs.existsSync("/tmp/real_crawler.pid")

    // Ultimele statistici crawler
    const crawlerStats = await db.get(`
      SELECT * FROM crawler_stats 
      ORDER BY timestamp DESC 
      LIMIT 1
    `)

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
      source: "real_database",
      timestamp: new Date().toISOString(),
      database_path: dbPath,
    })
  } catch (error) {
    console.error("Error in real ads API:", error)
    return NextResponse.json(
      {
        error: "Failed to fetch real data",
        message: error.message,
        source: "error",
      },
      { status: 500 },
    )
  }
}
