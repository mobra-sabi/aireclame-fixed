"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ArrowLeft, Search } from "lucide-react"

interface Ad {
  id: number
  video_id: string
  title: string
  channel: string
  views: number
  likes: number
  engagement_rate: number
  confidence_score: number
  ad_type: string
  duration: number
  created_at: string
}

export default function AdsPage() {
  const [ads, setAds] = useState<Ad[]>([])
  const [loading, setLoading] = useState(true)
  const [searchTerm, setSearchTerm] = useState("")

  useEffect(() => {
    const fetchData = async () => {
      try {
        const response = await fetch("/api/ads")
        const result = await response.json()
        setAds(result.recent_ads || [])
      } catch (error) {
        console.error("Error fetching ads:", error)
        // Date mock în caz de eroare
        setAds([
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
        ])
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  // Formatare dată
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("ro-RO", {
      day: "2-digit",
      month: "2-digit",
      year: "numeric",
    })
  }

  // Formatare durată
  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`
  }

  // Filtrare reclame după termen de căutare
  const filteredAds = ads.filter(
    (ad) =>
      ad.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ad.channel.toLowerCase().includes(searchTerm.toLowerCase()) ||
      ad.ad_type.toLowerCase().includes(searchTerm.toLowerCase()),
  )

  return (
    <div className="p-6">
      <div className="flex flex-col md:flex-row justify-between items-start md:items-center mb-6 gap-4">
        <div className="flex items-center">
          <Link href="/dashboard">
            <Button variant="outline" size="icon" className="mr-4">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <h1 className="text-3xl font-bold">Toate Reclamele</h1>
        </div>
        <div className="relative w-full md:w-64">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Caută reclame..."
            className="pl-8"
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
          />
        </div>
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Reclame ({filteredAds.length})</CardTitle>
        </CardHeader>
        <CardContent>
          {loading ? (
            <p>Se încarcă reclamele...</p>
          ) : filteredAds.length === 0 ? (
            <p>Nu există reclame care să corespundă criteriilor de căutare.</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b">
                    <th className="text-left py-2 px-2">Titlu</th>
                    <th className="text-left py-2 px-2">Canal</th>
                    <th className="text-left py-2 px-2">Tip</th>
                    <th className="text-left py-2 px-2">Durată</th>
                    <th className="text-left py-2 px-2">Vizualizări</th>
                    <th className="text-left py-2 px-2">Confidence</th>
                    <th className="text-left py-2 px-2">Data</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredAds.map((ad) => (
                    <tr key={ad.id} className="border-b hover:bg-muted/50">
                      <td className="py-2 px-2 max-w-[200px] truncate">{ad.title}</td>
                      <td className="py-2 px-2">{ad.channel}</td>
                      <td className="py-2 px-2 capitalize">{ad.ad_type.replace("_", " ")}</td>
                      <td className="py-2 px-2">{formatDuration(ad.duration)}</td>
                      <td className="py-2 px-2">{ad.views.toLocaleString()}</td>
                      <td className="py-2 px-2">{(ad.confidence_score * 100).toFixed(0)}%</td>
                      <td className="py-2 px-2">{formatDate(ad.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
