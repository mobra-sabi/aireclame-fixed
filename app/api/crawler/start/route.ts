import { type NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    // Încearcă să parseze body-ul
    let config = { channels: [], keywords: [], maxVideos: 10 }
    try {
      const body = await request.json()
      config = { ...config, ...body }
    } catch (parseError) {
      console.error("Eroare parsare body:", parseError)
      // Continuă cu configurația implicită
    }

    // Verifică dacă crawler-ul rulează deja
    try {
      const fs = await import("fs")
      const pidFile = "/tmp/crawler.pid"

      if (fs.existsSync(pidFile)) {
        return NextResponse.json({
          error: "Crawler-ul rulează deja",
          status: "running",
        })
      }

      // Simulează pornirea crawler-ului
      const pid = Math.floor(Math.random() * 10000) + 1000
      fs.writeFileSync(pidFile, pid.toString())

      return NextResponse.json({
        message: "Crawler pornit cu succes (simulat)",
        pid: pid,
        status: "started",
        config: config,
      })
    } catch (fsError) {
      console.error("Eroare sistem fișiere:", fsError)
      return NextResponse.json({
        message: "Crawler pornit în mod simulat",
        pid: Math.floor(Math.random() * 10000) + 1000,
        status: "started",
        config: config,
      })
    }
  } catch (error) {
    console.error("Eroare pornire crawler:", error)
    return NextResponse.json({
      error: "Eroare la pornirea crawler-ului: " + error.message,
      status: "error",
    })
  }
}
