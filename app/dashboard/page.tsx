"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowRight, RefreshCw, Loader2, AlertCircle, Play, Square, Database } from "lucide-react"

interface RealDashboardData {
  stats: {
    total_ads: number
    unique_channels: number
    avg_confidence: number
    ads_last_24h: number
  }
  recent_ads: any[]
  ad_types: any[]
  hourly_stats: any[]
  top_channels: any[]
  crawler_status: {
    running: boolean
    stats: any
  }
  source: string
  timestamp: string
  database_path: string
}

export default function RealDashboardPage() {
  const [data, setData] = useState<RealDashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<string>("")
  const [error, setError] = useState<string | null>(null)

  const fetchRealData = async (showLoading = true) => {
    if (showLoading) setRefreshing(true)
    setError(null)

    try {
      const response = await fetch("/api/ads/real", {
        cache: "no-store",
        headers: { "Cache-Control": "no-cache" },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`)
      }

      const result = await response.json()
      setData(result)
      setLastUpdate(new Date().toLocaleTimeString("ro-RO"))

      if (result.source === "no_real_database") {
        setError("Baza de date reală nu există. Pornește crawler-ul real pentru a colecta date de la YouTube.")
      } else if (result.source === "error") {
        setError(result.message)
      }
    } catch (fetchError) {
      console.error("Error fetching REAL data:", fetchError)
      setError(fetchError.message)
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchRealData()

    // Auto-refresh la fiecare 30 de secunde pentru date REALE
    const interval = setInterval(() => {
      fetchRealData(false)
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleDateString("ro-RO", {
      day: "2-digit",
      month: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
    })
  }

  const formatDuration = (seconds: number) => {
    const minutes = Math.floor(seconds / 60)
    const remainingSeconds = seconds % 60
    return `${minutes}:${remainingSeconds.toString().padStart(2, "0")}`
  }

  const getSourceBadge = (source: string) => {
    switch (source) {
      case "real_database":
        return <Badge className="bg-green-100 text-green-800">🎯 REAL DATA</Badge>
      case "no_real_database":
        return <Badge variant="destructive">❌ NO DATABASE</Badge>
      case "error":
        return <Badge variant="destructive">❌ ERROR</Badge>
      default:
        return <Badge variant="outline">❓ UNKNOWN</Badge>
    }
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold">🎯 AireClame - REAL YouTube Data</h1>
          <p className="text-sm text-gray-600 mt-1">Folosește API-uri REALE YouTube - FĂRĂ date fake</p>
          {lastUpdate && (
            <div className="flex items-center gap-2 mt-2">
              <p className="text-sm text-gray-600">Ultima actualizare: {lastUpdate}</p>
              {data?.source && getSourceBadge(data.source)}
              {data?.crawler_status && (
                <Badge variant={data.crawler_status.running ? "default" : "secondary"}>
                  Crawler: {data.crawler_status.running ? "🟢 ACTIV" : "🔴 OPRIT"}
                </Badge>
              )}
            </div>
          )}
        </div>
        <div className="flex gap-2">
          <Button
            variant="outline"
            onClick={() => fetchRealData()}
            disabled={refreshing}
            className="flex items-center gap-2"
          >
            {refreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
            Refresh Real Data
          </Button>
          <Link href="/dashboard/crawler">
            <Button variant="outline" className="flex items-center gap-2">
              {data?.crawler_status?.running ? <Square className="h-4 w-4" /> : <Play className="h-4 w-4" />}
              Control Crawler
            </Button>
          </Link>
        </div>
      </div>

      {error && (
        <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg flex items-start gap-3">
          <AlertCircle className="h-5 w-5 text-red-600 mt-0.5" />
          <div>
            <p className="text-sm text-red-800 font-medium">
              <strong>EROARE:</strong> {error}
            </p>
            {data?.source === "no_real_database" && (
              <div className="text-xs text-red-700 mt-2 space-y-1">
                <p>Pentru a porni crawler-ul REAL:</p>
                <code className="bg-red-100 px-2 py-1 rounded">./scripts/start_real_crawler.sh start</code>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Statistici REALE */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
        <Card className="border-green-200">
          <CardHeader className="pb-2">
            <CardTitle className="flex items-center gap-2">
              <Database className="h-4 w-4" />
              Reclame REALE
            </CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-green-600">{data?.stats.total_ads || 0}</p>
            <p className="text-sm text-muted-foreground">Din YouTube API</p>
          </CardContent>
        </Card>

        <Card className="border-blue-200">
          <CardHeader className="pb-2">
            <CardTitle>Ultimele 24h</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-blue-600">{data?.stats.ads_last_24h || 0}</p>
            <p className="text-sm text-muted-foreground">Reclame noi REALE</p>
          </CardContent>
        </Card>

        <Card className="border-purple-200">
          <CardHeader className="pb-2">
            <CardTitle>Canale REALE</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-purple-600">{data?.stats.unique_channels || 0}</p>
            <p className="text-sm text-muted-foreground">Canale YouTube</p>
          </CardContent>
        </Card>

        <Card className="border-orange-200">
          <CardHeader className="pb-2">
            <CardTitle>Acuratețe AI</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-3xl font-bold text-orange-600">
              {((data?.stats.avg_confidence || 0) * 100).toFixed(1)}%
            </p>
            <p className="text-sm text-muted-foreground">Detectare reclame</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Reclame REALE recente */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                🎯 Reclame REALE de pe YouTube
                <Badge variant="outline" className="text-xs">
                  Live
                </Badge>
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="flex items-center justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin mr-2" />
                  <span>Se încarcă date REALE...</span>
                </div>
              ) : data?.recent_ads?.length === 0 ? (
                <div className="text-center py-8">
                  <Database className="h-12 w-12 text-gray-400 mx-auto mb-4" />
                  <p className="text-gray-500 font-medium">Nu există reclame REALE în baza de date</p>
                  <p className="text-sm text-gray-400 mt-2">Pornește crawler-ul pentru a colecta de la YouTube</p>
                  <Button variant="outline" className="mt-4" asChild>
                    <Link href="/dashboard/crawler">Pornește Crawler</Link>
                  </Button>
                </div>
              ) : (
                <>
                  <div className="overflow-x-auto">
                    <table className="w-full">
                      <thead>
                        <tr className="border-b">
                          <th className="text-left py-2 px-2">Titlu REAL</th>
                          <th className="text-left py-2 px-2">Canal YouTube</th>
                          <th className="text-left py-2 px-2">Tip</th>
                          <th className="text-left py-2 px-2">Views</th>
                          <th className="text-left py-2 px-2">Confidence</th>
                          <th className="text-left py-2 px-2">Data</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data?.recent_ads?.slice(0, 10).map((ad) => (
                          <tr key={ad.id} className="border-b hover:bg-green-50">
                            <td className="py-2 px-2 max-w-[200px] truncate font-medium">{ad.title}</td>
                            <td className="py-2 px-2 text-blue-600">{ad.channel}</td>
                            <td className="py-2 px-2 capitalize text-sm">{ad.ad_type?.replace("_", " ") || "N/A"}</td>
                            <td className="py-2 px-2 text-sm">{ad.views?.toLocaleString() || 0}</td>
                            <td className="py-2 px-2">
                              <Badge variant={ad.confidence_score > 0.7 ? "default" : "secondary"}>
                                {(ad.confidence_score * 100).toFixed(0)}%
                              </Badge>
                            </td>
                            <td className="py-2 px-2 text-sm">{formatDate(ad.created_at)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <div className="mt-4 text-right">
                    <Link
                      href="/dashboard/ads"
                      className="text-green-600 hover:text-green-800 flex items-center justify-end"
                    >
                      Vezi toate reclamele REALE <ArrowRight className="ml-1 h-4 w-4" />
                    </Link>
                  </div>
                </>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Tipuri REALE de reclame */}
        <div>
          <Card>
            <CardHeader>
              <CardTitle>Tipuri REALE de Reclame</CardTitle>
            </CardHeader>
            <CardContent>
              {data?.ad_types?.length === 0 ? (
                <p className="text-gray-500 text-center py-4">Nu există date</p>
              ) : (
                <div className="space-y-3">
                  {data?.ad_types?.slice(0, 8).map((type, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="capitalize text-sm font-medium">
                        {type.ad_type?.replace("_", " ") || "Unknown"}
                      </span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-bold text-green-600">{type.count}</span>
                        <div className="w-16 bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-green-600 h-2 rounded-full"
                            style={{
                              width: `${Math.min((type.count / (data?.stats.total_ads || 1)) * 100, 100)}%`,
                            }}
                          ></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
              <div className="mt-4 text-right">
                <Link
                  href="/dashboard/analysis"
                  className="text-green-600 hover:text-green-800 flex items-center justify-end"
                >
                  Analiză detaliată <ArrowRight className="ml-1 h-4 w-4" />
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Status crawler */}
      {data?.crawler_status && (
        <div className="mt-6">
          <Card>
            <CardHeader>
              <CardTitle>Status Crawler REAL</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <p className="text-sm text-gray-600">Status</p>
                  <p className="font-medium">
                    {data.crawler_status.running ? "🟢 ACTIV - Colectează REAL" : "🔴 OPRIT"}
                  </p>
                </div>
                {data.crawler_status.stats && (
                  <>
                    <div>
                      <p className="text-sm text-gray-600">Videos verificate</p>
                      <p className="font-medium">{data.crawler_status.stats.videos_checked || 0}</p>
                    </div>
                    <div>
                      <p className="text-sm text-gray-600">API calls</p>
                      <p className="font-medium">{data.crawler_status.stats.api_calls || 0}</p>
                    </div>
                  </>
                )}
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  )
}
