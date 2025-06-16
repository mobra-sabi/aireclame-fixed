"use client"

import { useState, useEffect } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ArrowLeft, Play, Square, Loader2, RefreshCw } from "lucide-react"
import { Alert, AlertDescription } from "@/components/ui/alert"
import Link from "next/link"

interface CrawlerStatus {
  status: "running" | "stopped"
  pid?: string
  stats?: {
    videosProcessed: number
    adsFound: number
    errors: number
  }
  message: string
}

export default function CrawlerMonitorPage() {
  const [crawlerStatus, setCrawlerStatus] = useState<CrawlerStatus>({
    status: "stopped",
    message: "Verificare status...",
  })
  const [loading, setLoading] = useState(false)
  const [refreshing, setRefreshing] = useState(false)

  // Verifică statusul crawler-ului la încărcare
  useEffect(() => {
    checkCrawlerStatus()

    // Actualizează statusul la fiecare 10 secunde
    const interval = setInterval(() => {
      checkCrawlerStatus(true)
    }, 10000)

    return () => clearInterval(interval)
  }, [])

  const checkCrawlerStatus = async (silent = false) => {
    if (!silent) setRefreshing(true)
    try {
      const response = await fetch("/api/crawler/status")
      const data = await response.json()
      setCrawlerStatus(data)
    } catch (error) {
      console.error("Eroare verificare status:", error)
    } finally {
      if (!silent) setRefreshing(false)
    }
  }

  const startCrawler = async () => {
    setLoading(true)
    try {
      const response = await fetch("/api/crawler/start", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          channels: ["UCrAav-QgGtjdVEmr9DtM3rQ", "UCYfdidRxbB8Qhf0Nx7ioOYw"],
          keywords: ["reclama", "publicitate", "promo", "advertisement"],
          maxVideos: 50,
        }),
      })

      const data = await response.json()

      if (response.ok) {
        setCrawlerStatus({ status: "running", message: data.message, pid: data.pid })
      } else {
        alert(`Eroare: ${data.error}`)
      }
    } catch (error) {
      console.error("Eroare pornire crawler:", error)
      alert("Eroare la pornirea crawler-ului")
    } finally {
      setLoading(false)
    }
  }

  const stopCrawler = async () => {
    setLoading(true)
    try {
      const response = await fetch("/api/crawler/stop", { method: "POST" })
      const data = await response.json()
      setCrawlerStatus({ status: "stopped", message: data.message })
    } catch (error) {
      console.error("Eroare oprire crawler:", error)
      alert("Eroare la oprirea crawler-ului")
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
            <h1 className="text-3xl font-bold text-gray-900">Monitorizare Crawler</h1>
            <p className="text-gray-600">Controlează și monitorizează procesul de crawling</p>
          </div>
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => checkCrawlerStatus()} disabled={refreshing}>
              {refreshing ? <Loader2 className="h-4 w-4 animate-spin mr-2" /> : <RefreshCw className="h-4 w-4 mr-2" />}
              Refresh
            </Button>
            <Link href="/dashboard">
              <Button variant="outline" className="flex items-center gap-2">
                <ArrowLeft className="h-4 w-4" />
                Înapoi la Dashboard
              </Button>
            </Link>
          </div>
        </div>

        {/* Status Card */}
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              Status Crawler
              <Badge variant={crawlerStatus.status === "running" ? "default" : "secondary"}>
                {crawlerStatus.status === "running" ? "Activ" : "Oprit"}
              </Badge>
            </CardTitle>
            <CardDescription>{crawlerStatus.message}</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col gap-4">
              {crawlerStatus.status === "running" && crawlerStatus.stats && (
                <div className="grid grid-cols-3 gap-4">
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">{crawlerStatus.stats.videosProcessed}</div>
                      <p className="text-sm text-muted-foreground">Videouri procesate</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">{crawlerStatus.stats.adsFound}</div>
                      <p className="text-sm text-muted-foreground">Reclame detectate</p>
                    </CardContent>
                  </Card>
                  <Card>
                    <CardContent className="pt-6">
                      <div className="text-2xl font-bold">{crawlerStatus.stats.errors}</div>
                      <p className="text-sm text-muted-foreground">Erori</p>
                    </CardContent>
                  </Card>
                </div>
              )}

              <div className="flex gap-2">
                {crawlerStatus.status === "stopped" ? (
                  <Button onClick={startCrawler} disabled={loading} className="flex items-center gap-2">
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
                    Pornește Crawler
                  </Button>
                ) : (
                  <Button
                    onClick={stopCrawler}
                    disabled={loading}
                    variant="destructive"
                    className="flex items-center gap-2"
                  >
                    {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Square className="h-4 w-4" />}
                    Oprește Crawler
                  </Button>
                )}
              </div>

              {crawlerStatus.status === "running" && (
                <Alert>
                  <AlertDescription>
                    Crawler-ul rulează cu PID: {crawlerStatus.pid}. Procesul poate dura câteva minute sau ore, în
                    funcție de configurație.
                  </AlertDescription>
                </Alert>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Logs Card */}
        <Card>
          <CardHeader>
            <CardTitle>Logs Crawler</CardTitle>
            <CardDescription>Ultimele evenimente înregistrate</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="bg-black text-green-400 p-4 rounded-md font-mono text-sm h-64 overflow-y-auto">
              {crawlerStatus.status === "running" ? (
                <>
                  <p>
                    [{new Date().toISOString()}] Crawler pornit cu PID: {crawlerStatus.pid}
                  </p>
                  <p>[{new Date().toISOString()}] Inițializare proces de crawling...</p>
                  <p>[{new Date().toISOString()}] Căutare videouri pe YouTube...</p>
                  {crawlerStatus.stats && crawlerStatus.stats.videosProcessed > 0 && (
                    <>
                      <p>
                        [{new Date().toISOString()}] Procesate {crawlerStatus.stats.videosProcessed} videouri până acum
                      </p>
                      <p>
                        [{new Date().toISOString()}] Detectate {crawlerStatus.stats.adsFound} reclame până acum
                      </p>
                      {crawlerStatus.stats.errors > 0 && (
                        <p className="text-red-400">
                          [{new Date().toISOString()}] Întâmpinate {crawlerStatus.stats.errors} erori
                        </p>
                      )}
                    </>
                  )}
                </>
              ) : (
                <p>[{new Date().toISOString()}] Crawler oprit. Pornește crawler-ul pentru a vedea logs.</p>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
