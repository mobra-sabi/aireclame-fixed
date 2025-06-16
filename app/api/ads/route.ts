import { NextResponse } from "next/server"

// Date mock pentru a asigura că avem întotdeauna un răspuns
const mockData = {
  stats: {
    total_ads: 127,
    unique_channels: 18,
    avg_confidence: 0.87,
    ads_last_24h: 12,
  },
  recent_ads: [
    {
      id: 1,
      video_id: "sample1",
      title: "Reclamă Auto 2025 - Mașina Viitorului",
      channel: "AutoChannel",
      views: 15000,
      likes: 750,
      engagement_rate: 0.05,
      confidence_score: 0.95,
      ad_type: "automotive",
      duration: 30,
      created_at: "2025-01-15T10:00:00Z",
    },
    {
      id: 2,
      video_id: "sample2",
      title: "Publicitate Telefon Nou - Tehnologie Avansată",
      channel: "TechChannel",
      views: 25000,
      likes: 1200,
      engagement_rate: 0.048,
      confidence_score: 0.92,
      ad_type: "technology",
      duration: 45,
      created_at: "2025-01-16T14:30:00Z",
    },
    {
      id: 3,
      video_id: "sample3",
      title: "Reclamă Băutură Răcoritoare - Vara 2025",
      channel: "DrinkChannel",
      views: 8000,
      likes: 320,
      engagement_rate: 0.04,
      confidence_score: 0.88,
      ad_type: "food_beverage",
      duration: 20,
      created_at: "2025-01-17T16:45:00Z",
    },
    {
      id: 4,
      video_id: "sample4",
      title: "Publicitate Magazin Online - Reduceri Speciale",
      channel: "ShopChannel",
      views: 12000,
      likes: 480,
      engagement_rate: 0.04,
      confidence_score: 0.91,
      ad_type: "retail",
      duration: 25,
      created_at: "2025-01-18T09:15:00Z",
    },
    {
      id: 5,
      video_id: "sample5",
      title: "Reclamă Restaurant - Mâncare Delicioasă",
      channel: "FoodChannel",
      views: 18000,
      likes: 900,
      engagement_rate: 0.05,
      confidence_score: 0.89,
      ad_type: "food_beverage",
      duration: 35,
      created_at: "2025-01-19T12:00:00Z",
    },
  ],
  ad_types: [
    { ad_type: "automotive", count: 32 },
    { ad_type: "technology", count: 45 },
    { ad_type: "food_beverage", count: 28 },
    { ad_type: "retail", count: 22 },
  ],
  system_stats: {
    gpu_usage: [
      { time: "08:00", usage: 15 },
      { time: "09:00", usage: 45 },
      { time: "10:00", usage: 78 },
      { time: "11:00", usage: 92 },
      { time: "12:00", usage: 65 },
      { time: "13:00", usage: 48 },
    ],
    cpu_usage: 42,
    memory_usage: 68,
    storage_usage: 37,
    active_processes: 3,
  },
}

export async function GET() {
  // Returnează întotdeauna datele mock pentru a evita erorile
  return NextResponse.json(mockData)
}
