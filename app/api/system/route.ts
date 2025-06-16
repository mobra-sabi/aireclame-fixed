import { NextResponse } from "next/server"

export async function GET() {
  // Date mock pentru statistici sistem
  const systemStats = {
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
    gpus: [
      {
        name: "NVIDIA RTX 4090",
        memory_total: "24 GB",
        memory_used: "8.2 GB",
        temperature: 65,
        utilization: 38,
      },
      {
        name: "NVIDIA RTX 4090",
        memory_total: "24 GB",
        memory_used: "6.7 GB",
        temperature: 62,
        utilization: 31,
      },
    ],
    processes: [
      {
        name: "crawler.py",
        pid: 12345,
        cpu: 28.5,
        memory: 4.2,
        runtime: "2h 15m",
        status: "running",
      },
      {
        name: "analyzer.py",
        pid: 12346,
        cpu: 15.3,
        memory: 2.8,
        runtime: "1h 45m",
        status: "running",
      },
      {
        name: "next-server",
        pid: 12347,
        cpu: 3.2,
        memory: 1.5,
        runtime: "5h 30m",
        status: "running",
      },
    ],
  }

  return NextResponse.json(systemStats)
}
