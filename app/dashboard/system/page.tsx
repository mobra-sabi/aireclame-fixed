"use client"

import { useEffect, useState } from "react"
import Link from "next/link"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Badge } from "@/components/ui/badge"
import { ArrowLeft, Cpu, HardDrive, MemoryStickIcon as Memory, Thermometer, RefreshCw, Loader2 } from "lucide-react"

interface GPU {
  index: number
  name: string
  memory_used: string
  memory_total: string
  temperature: number
  utilization: number
}

interface Process {
  name: string
  pid: number
  cpu: number
  memory: number
  runtime?: string
  status?: string
}

interface SystemStats {
  gpu_usage: { time: string; usage: number }[]
  cpu_usage: number
  memory_usage: number
  storage_usage: number
  active_processes: number
  gpus: GPU[]
  processes: Process[]
  timestamp: string
  source?: string
  error?: string
}

export default function SystemPage() {
  const [systemStats, setSystemStats] = useState<SystemStats | null>(null)
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [lastUpdate, setLastUpdate] = useState<string>("")

  const fetchSystemData = async (showLoading = true) => {
    if (showLoading) setRefreshing(true)

    try {
      // Încearcă să folosească API-ul real
      const response = await fetch("/api/system/real", {
        cache: "no-store",
        headers: {
          "Cache-Control": "no-cache",
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const data = await response.json()
      setSystemStats(data)
      setLastUpdate(new Date().toLocaleTimeString("ro-RO"))
    } catch (error) {
      console.error("Error fetching real system data, trying fallback:", error)

      // Fallback la API-ul mock
      try {
        const fallbackResponse = await fetch("/api/system")
        const fallbackData = await fallbackResponse.json()
        setSystemStats({
          ...fallbackData,
          source: "fallback",
          error: error.message,
        })
        setLastUpdate(new Date().toLocaleTimeString("ro-RO"))
      } catch (fallbackError) {
        console.error("Fallback also failed:", fallbackError)
      }
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }

  useEffect(() => {
    fetchSystemData()

    // Auto-refresh la fiecare 30 de secunde
    const interval = setInterval(() => {
      fetchSystemData(false)
    }, 30000)

    return () => clearInterval(interval)
  }, [])

  const getMemoryUsagePercent = (gpu: GPU) => {
    const used = Number.parseFloat(gpu.memory_used.replace(/[^\d.]/g, ""))
    const total = Number.parseFloat(gpu.memory_total.replace(/[^\d.]/g, ""))
    return total > 0 ? (used / total) * 100 : 0
  }

  const getTemperatureColor = (temp: number) => {
    if (temp > 80) return "bg-red-200 [&>div]:bg-red-500"
    if (temp > 70) return "bg-yellow-200 [&>div]:bg-yellow-500"
    return "bg-green-200 [&>div]:bg-green-500"
  }

  return (
    <div className="p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center">
          <Link href="/dashboard">
            <Button variant="outline" size="icon" className="mr-4">
              <ArrowLeft className="h-4 w-4" />
            </Button>
          </Link>
          <div>
            <h1 className="text-3xl font-bold">Detalii Sistem</h1>
            {lastUpdate && (
              <p className="text-sm text-gray-600">
                Ultima actualizare: {lastUpdate}
                {systemStats?.source && (
                  <Badge variant="outline" className="ml-2">
                    {systemStats.source === "fallback" ? "Mock Data" : "Live Data"}
                  </Badge>
                )}
              </p>
            )}
          </div>
        </div>
        <Button
          variant="outline"
          onClick={() => fetchSystemData()}
          disabled={refreshing}
          className="flex items-center gap-2"
        >
          {refreshing ? <Loader2 className="h-4 w-4 animate-spin" /> : <RefreshCw className="h-4 w-4" />}
          Refresh
        </Button>
      </div>

      {systemStats?.error && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <p className="text-sm text-yellow-800">
            <strong>Atenție:</strong> Nu s-au putut obține date reale de la sistem. Eroare: {systemStats.error}
          </p>
        </div>
      )}

      {loading ? (
        <p>Se încarcă datele sistemului...</p>
      ) : (
        <>
          {/* Statistici generale */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center">
                  <Cpu className="mr-2 h-4 w-4" /> CPU
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{systemStats?.cpu_usage?.toFixed(1)}%</p>
                <Progress value={systemStats?.cpu_usage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center">
                  <Memory className="mr-2 h-4 w-4" /> Memorie
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{systemStats?.memory_usage?.toFixed(1)}%</p>
                <Progress value={systemStats?.memory_usage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle className="flex items-center">
                  <HardDrive className="mr-2 h-4 w-4" /> Storage
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{systemStats?.storage_usage?.toFixed(1)}%</p>
                <Progress value={systemStats?.storage_usage} className="mt-2" />
              </CardContent>
            </Card>

            <Card>
              <CardHeader className="pb-2">
                <CardTitle>Procese Active</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-3xl font-bold">{systemStats?.active_processes}</p>
              </CardContent>
            </Card>
          </div>

          {/* Utilizare GPU */}
          <Card className="mb-6">
            <CardHeader>
              <CardTitle>Utilizare GPU în timp</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="h-[200px] flex items-end gap-2">
                {systemStats?.gpu_usage?.map((point, i) => (
                  <div key={i} className="flex flex-col items-center flex-1">
                    <div
                      className="bg-blue-500 w-full rounded-t transition-all duration-300"
                      style={{ height: `${Math.max(point.usage, 2)}%` }}
                    ></div>
                    <span className="text-xs mt-1">{point.time}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Detalii GPU */}
          {systemStats?.gpus && systemStats.gpus.length > 0 && (
            <Card className="mb-6">
              <CardHeader>
                <CardTitle>Detalii GPU</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {systemStats.gpus.map((gpu, index) => (
                    <Card key={index}>
                      <CardHeader className="pb-2">
                        <CardTitle className="text-lg">
                          GPU {gpu.index}: {gpu.name}
                        </CardTitle>
                      </CardHeader>
                      <CardContent>
                        <div className="space-y-4">
                          <div>
                            <div className="flex justify-between mb-1">
                              <span>Memorie</span>
                              <span>
                                {gpu.memory_used} / {gpu.memory_total}
                              </span>
                            </div>
                            <Progress value={getMemoryUsagePercent(gpu)} />
                          </div>

                          <div>
                            <div className="flex justify-between mb-1">
                              <span className="flex items-center">
                                <Thermometer className="mr-1 h-4 w-4" /> Temperatură
                              </span>
                              <span>{gpu.temperature}°C</span>
                            </div>
                            <Progress
                              value={(gpu.temperature / 100) * 100}
                              className={getTemperatureColor(gpu.temperature)}
                            />
                          </div>

                          <div>
                            <div className="flex justify-between mb-1">
                              <span>Utilizare</span>
                              <span>{gpu.utilization}%</span>
                            </div>
                            <Progress value={gpu.utilization} />
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Procese active */}
          {systemStats?.processes && systemStats.processes.length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle>Procese Active</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b">
                        <th className="text-left py-2 px-2">Nume</th>
                        <th className="text-left py-2 px-2">PID</th>
                        <th className="text-left py-2 px-2">CPU</th>
                        <th className="text-left py-2 px-2">Memorie</th>
                        <th className="text-left py-2 px-2">Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {systemStats.processes.map((process, index) => (
                        <tr key={index} className="border-b hover:bg-muted/50">
                          <td className="py-2 px-2 font-mono text-sm">{process.name}</td>
                          <td className="py-2 px-2">{process.pid}</td>
                          <td className="py-2 px-2">{process.cpu?.toFixed(1)}%</td>
                          <td className="py-2 px-2">{process.memory?.toFixed(1)}%</td>
                          <td className="py-2 px-2">
                            <span className="px-2 py-1 rounded text-xs bg-green-100 text-green-800">
                              {process.status || "running"}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}
    </div>
  )
}
