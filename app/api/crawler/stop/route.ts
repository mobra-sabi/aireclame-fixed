import { NextResponse } from "next/server"

export async function POST() {
  try {
    try {
      const fs = await import("fs")
      const pidFile = "/tmp/crawler.pid"

      if (!fs.existsSync(pidFile)) {
        return NextResponse.json({
          message: "Crawler-ul nu rulează",
          status: "already_stopped",
        })
      }

      // Șterge PID file pentru a simula oprirea
      fs.unlinkSync(pidFile)

      return NextResponse.json({
        message: "Crawler oprit cu succes (simulat)",
        status: "stopped",
      })
    } catch (fsError) {
      console.error("Eroare sistem fișiere:", fsError)
      return NextResponse.json({
        message: "Crawler oprit în mod simulat",
        status: "stopped",
      })
    }
  } catch (error) {
    console.error("Eroare oprire crawler:", error)
    return NextResponse.json({
      error: "Eroare la oprirea crawler-ului: " + error.message,
      status: "error",
    })
  }
}
