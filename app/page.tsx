"use client"

import { useState, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { BarChart3, Activity, AlertCircle } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"

interface Stats {
  total_ads: number
  unique_channels: number
  avg_confidence: number
  ads_last_24h: number
}

export default function HomePage() {
  const [stats, setStats] = useState<Stats>({
    total_ads: 0,
    unique_channels: 0,
    avg_confidence: 0,
    ads_last_24h: 0,
  })
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchData() {
      try {
        setError(null)

        // Try multiple API endpoints
        const apiUrls = [
          `${process.env.NEXT_PUBLIC_API_URL}/api/ads`,
          "/api/ads",
          "https://15d1-92-80-101-26.ngrok-free.app/api/ads",
        ].filter(Boolean)

        let lastError: Error | null = null

        for (const url of apiUrls) {
          try {
            console.log(`Trying to fetch from: ${url}`)

            const response = await fetch(url, {
              method: "GET",
              headers: {
                "Content-Type": "application/json",
                Accept: "application/json",
                // Add ngrok bypass header if needed
                "ngrok-skip-browser-warning": "true",
              },
              // Add timeout
              signal: AbortSignal.timeout(10000), // 10 second timeout
            })

            if (!response.ok) {
              throw new Error(`HTTP ${response.status}: ${response.statusText}`)
            }

            const data = await response.json()
            console.log("Successfully fetched data:", data)

            if (data.stats) {
              setStats(data.stats)
              return // Success, exit the loop
            }
          } catch (err) {
            console.warn(`Failed to fetch from ${url}:`, err)
            lastError = err as Error
            continue // Try next URL
          }
        }

        // If all URLs failed, throw the last error
        throw lastError || new Error("All API endpoints failed")
      } catch (error) {
        console.error("Error fetching data:", error)
        setError(error instanceof Error ? error.message : "Unknown error occurred")

        // Use mock data as fallback
        setStats({
          total_ads: 127,
          unique_channels: 18,
          avg_confidence: 0.87,
          ads_last_24h: 12,
        })
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100">
      <div className="container mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">AireClame</h1>
          <p className="text-xl text-gray-600">Platformă de analiză a reclamelor de pe YouTube</p>
        </div>

        {/* Error Alert */}
        {error && (
          <Alert variant="destructive" className="mb-8">
            <AlertCircle className="h-4 w-4" />
            <AlertDescription>
              <strong>Conexiune API:</strong> {error}
              <br />
              <span className="text-sm">Se folosesc date demo. Verifică că ngrok rulează pe server.</span>
            </AlertDescription>
          </Alert>
        )}

        {/* Status Bar */}
        <div className="mb-8">
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Activity className="h-5 w-5" />
                Status Sistem
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <Badge variant={error ? "destructive" : "default"}>
                    {error ? "API Offline" : "Conectat la server"}
                  </Badge>
                  <span className="text-sm text-gray-600">
                    API: {process.env.NEXT_PUBLIC_API_URL || "https://15d1-92-80-101-26.ngrok-free.app"}
                  </span>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Main Cards */}
        <div className="grid md:grid-cols-2 gap-8 mb-12">
          {/* Dashboard Card */}
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle>Dashboard</CardTitle>
              <CardDescription>
                Vizualizează statistici și analize detaliate despre reclamele descoperite.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-semibold text-2xl text-blue-600">
                    {loading ? "..." : stats.total_ads.toLocaleString()}
                  </div>
                  <div className="text-gray-600">Total reclame</div>
                </div>
                <div>
                  <div className="font-semibold text-2xl text-green-600">{loading ? "..." : stats.ads_last_24h}</div>
                  <div className="text-gray-600">Ultimele 24h</div>
                </div>
                <div>
                  <div className="font-semibold text-2xl text-purple-600">
                    {loading ? "..." : stats.unique_channels}
                  </div>
                  <div className="text-gray-600">Canale unice</div>
                </div>
                <div>
                  <div className="font-semibold text-2xl text-orange-600">
                    {loading ? "..." : `${(stats.avg_confidence * 100).toFixed(1)}%`}
                  </div>
                  <div className="text-gray-600">Confidence avg</div>
                </div>
              </div>
              <Link href="/dashboard">
                <Button className="w-full flex items-center gap-2">
                  <BarChart3 className="h-4 w-4" />
                  Accesează Dashboard
                </Button>
              </Link>
            </CardContent>
          </Card>

          {/* Server Status Card */}
          <Card className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <CardTitle>Status Server</CardTitle>
              <CardDescription>Informații despre serverul de procesare și baza de date.</CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <div className="font-semibold text-2xl text-blue-600">{error ? "Offline" : "GPU"}</div>
                  <div className="text-gray-600">{error ? "Nu se poate conecta" : "Procesare activă"}</div>
                </div>
                <div>
                  <div className="font-semibold text-2xl text-green-600">{error ? "Offline" : "DB"}</div>
                  <div className="text-gray-600">{error ? "Nu se poate conecta" : "Conectat"}</div>
                </div>
              </div>
              <Link href="/dashboard/system">
                <Button className="w-full" variant="outline">
                  Verifică status server
                </Button>
              </Link>
            </CardContent>
          </Card>
        </div>

        {/* Debug Info (only in development) */}
        {process.env.NODE_ENV === "development" && (
          <Card className="mb-8">
            <CardHeader>
              <CardTitle>Debug Info</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-sm space-y-2">
                <div>
                  <strong>NEXT_PUBLIC_API_URL:</strong> {process.env.NEXT_PUBLIC_API_URL || "Not set"}
                </div>
                <div>
                  <strong>Error:</strong> {error || "None"}
                </div>
                <div>
                  <strong>Loading:</strong> {loading ? "Yes" : "No"}
                </div>
              </div>
            </CardContent>
          </Card>
        )}

        {/* Footer */}
        <div className="text-center text-gray-500 text-sm">
          © 2025 AireClame. Toate drepturile rezervate.
          {error && <span className="block mt-1 text-orange-600">Rulează în modul demo</span>}
        </div>
      </div>
    </div>
  )
}
