"use client"

import { useState, useEffect } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Play, Square, Loader2, RefreshCw, BarChart3, TrendingUp } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"

interface AnalysisStatus {
  status: "idle" | "running" | "completed" | "error"
  progress: number
  current_phase: string
  stats: {
    videos_found: number
    ads_detected: number
    errors: number
    api_calls: number
    elapsed_time: number
  }
  message: string
}

interface AnalysisResults {
  total_ads: number
  categories: { category: string; count: number; percentage: number }[]
  top_brands: { brand: string; ads: number; engagement: number }[]
  monthly_trends: { month: string; ads: number; growth: number }[]
  top_channels: { channel: string; ads: number; avg_views: number }[]
}

export default function AnalysisPage() {
  const [analysisStatus, setAnalysisStatus] = useState<AnalysisStatus>({
    status: "idle",
    progress: 0,
    current_phase: "Ready to start",
    stats: { videos_found: 0, ads_detected: 0, errors: 0, api_calls: 0, elapsed_time: 0 },
    message: "Click Start Analysis to begin comprehensive 2025 YouTube ads analysis",
  })
  const [results, setResults] = useState<AnalysisResults | null>(null)
  const [loading, setLoading] = useState(false)

  useEffect(() => {
    // Check if analysis is already running
    checkAnalysisStatus()

    // Poll status every 10 seconds if running
    const interval = setInterval(() => {
      if (analysisStatus.status === "running") {
        checkAnalysisStatus()
      }
    }, 10000)

    return () => clearInterval(interval)
  }, [analysisStatus.status])

  const checkAnalysisStatus = async () => {
    try {
      const response = await fetch("/api/analysis/status")
      const data = await response.json()
      setAnalysisStatus(data)

      if (data.status === "completed") {
        fetchResults()
      }
    } catch (error) {
      console.error("Error checking analysis status:", error)
    }
  }

  const fetchResults = async () => {
    try {
      const response = await fetch("/api/analysis/results")
      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error("Error fetching results:", error)
    }
  }

  const startAnalysis = async () => {
    setLoading(true)
    try {
      const response = await fetch("/api/analysis/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          year: 2025,
          comprehensive: true,
          categories: "all",
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setAnalysisStatus({
          status: "running",
          progress: 0,
          current_phase: "Initializing",
          stats: { videos_found: 0, ads_detected: 0, errors: 0, api_calls: 0, elapsed_time: 0 },
          message: data.message,
        })
      } else {
        alert(`Error: ${data.error}`)
      }
    } catch (error) {
      console.error("Error starting analysis:", error)
      alert("Error starting analysis")
    } finally {
      setLoading(false)
    }
  }

  const stopAnalysis = async () => {
    setLoading(true)
    try {
      const response = await fetch("/api/analysis/stop", { method: "POST" })
      const data = await response.json()
      setAnalysisStatus({ ...analysisStatus, status: "idle", message: data.message })
    } catch (error) {
      console.error("Error stopping analysis:", error)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-3xl font-bold text-gray-900">Analiză Comprehensivă 2025</h1>
            <p className="text-gray-600">Analizează toate reclamele YouTube din 2025</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={checkAnalysisStatus}>
              <RefreshCw className="h-4 w-4 mr-2" />
              Refresh
            </Button>
            <Link href="/dashboard">
              <Button variant="outline" className="flex items-center gap-2">
                <ArrowLeft className="h-4 w-4" />
                Înapoi
              </Button>
            </Link>
          </div>
        </div>

        {/* Analysis Control */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5" />
              Control Analiză
              <Badge variant={analysisStatus.status === "running" ? "default" : "secondary"}>
                {analysisStatus.status === "running" ? "În progres" : "Oprit"}
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div>
                <div className="flex justify-between items-center mb-2">
                  <span className="text-sm font-medium">{analysisStatus.current_phase}</span>
                  <span className="text-sm text-gray-500">{analysisStatus.progress}%</span>
                </div>
                <Progress value={analysisStatus.progress} className="h-2" />
              </div>

              <Alert>
                <AlertDescription>{analysisStatus.message}</AlertDescription>
              </Alert>

              {analysisStatus.status === "running" && (
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="text-center">
                    <div className="text-2xl font-bold text-blue-600">{analysisStatus.stats.videos_found}</div>
                    <div className="text-sm text-gray-600">Videos găsite</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-green-600">{analysisStatus.stats.ads_detected}</div>
                    <div className="text-sm text-gray-600">Reclame detectate</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-orange-600">{analysisStatus.stats.api_calls}</div>
                    <div className="text-sm text-gray-600">API calls</div>
                  </div>
                  <div className="text-center">
                    <div className="text-2xl font-bold text-purple-600">
                      {Math.floor(analysisStatus.stats.elapsed_time / 60)}m
                    </div>
                    <div className="text-sm text-gray-600">Timp scurs</div>
                  </div>
                </div>
              )}

              <div className="flex gap-2">
                {analysisStatus.status === "idle" || analysisStatus.status === "completed" ? (
                  <Button onClick={startAnalysis} disabled={loading} className="flex items-center gap-2">
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                    Începe Analiza 2025
                  </Button>
                ) : (
                  <Button
                    onClick={stopAnalysis}
                    disabled={loading}
                    variant="destructive"
                    className="flex items-center gap-2"
                  >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Square className="h-4 w-4" />}
                    Oprește Analiza
                  </Button>
                )}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Results */}
        {results && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Categories */}
            <Card>
              <CardHeader>
                <CardTitle>Categorii de Reclame</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {results.categories.map((cat, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="capitalize">{cat.category.replace("_", " ")}</span>
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-gray-600">{cat.count}</span>
                        <div className="w-20 bg-gray-200 rounded-full h-2">
                          <div className="bg-blue-600 h-2 rounded-full" style={{ width: `${cat.percentage}%` }}></div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Top Brands */}
            <Card>
              <CardHeader>
                <CardTitle>Top Branduri</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {results.top_brands.map((brand, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="font-medium">{brand.brand}</span>
                      <div className="text-right">
                        <div className="text-sm font-semibold">{brand.ads} reclame</div>
                        <div className="text-xs text-gray-600">{(brand.engagement * 100).toFixed(2)}% engagement</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Monthly Trends */}
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <TrendingUp className="h-5 w-5" />
                  Tendințe Lunare
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {results.monthly_trends.map((trend, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span>{trend.month}</span>
                      <div className="text-right">
                        <div className="text-sm font-semibold">{trend.ads} reclame</div>
                        <div className={`text-xs ${trend.growth >= 0 ? "text-green-600" : "text-red-600"}`}>
                          {trend.growth >= 0 ? "+" : ""}
                          {trend.growth.toFixed(1)}%
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>

            {/* Top Channels */}
            <Card>
              <CardHeader>
                <CardTitle>Top Canale</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {results.top_channels.map((channel, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="truncate max-w-[200px]">{channel.channel}</span>
                      <div className="text-right">
                        <div className="text-sm font-semibold">{channel.ads} reclame</div>
                        <div className="text-xs text-gray-600">{channel.avg_views.toLocaleString()} views avg</div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        )}
      </div>
    </div>
  )
}
