import { NextResponse } from "next/server"

export async function GET() {
  try {
    // Verifică dacă putem accesa sistemul de fișiere
    try {
      const fs = await import("fs")
      const pidFile = "/tmp/crawler.pid"

      if (!fs.existsSync(pidFile)) {
        return NextResponse.json({
          status: "stopped",
          message: "Crawler-ul nu rulează",
        })
      }

      const pid = fs.readFileSync(pidFile, "utf8").trim()

      try {
        // Verifică dacă procesul rulează
        const { exec } = await import("child_process")
        const { promisify } = await import("util")
        const execAsync = promisify(exec)

        await execAsync(`ps -p ${pid}`)

        // Simulează statistici pentru crawler
        const stats = {
          videosProcessed: Math.floor(Math.random() * 100),
          adsFound: Math.floor(Math.random() * 50),
          errors: Math.floor(Math.random() * 10),
        }

        return NextResponse.json({
          status: "running",
          pid: pid,
          stats: stats,
          message: "Crawler-ul rulează activ",
        })
      } catch {
        // Procesul nu rulează, șterge PID file
        fs.unlinkSync(pidFile)
        return NextResponse.json({
          status: "stopped",
          message: "Crawler-ul s-a oprit",
        })
      }
    } catch (fsError) {
      console.error("Eroare acces sistem fișiere:", fsError)
      // Returnează date mock dacă nu putem accesa sistemul de fișiere
      return NextResponse.json({
        status: "unknown",
        message: "Nu se poate determina statusul crawler-ului",
        error: fsError.message,
      })
    }
  } catch (error) {
    console.error("Eroare generală:", error)
    // Asigură-te că returnăm întotdeauna un JSON valid
    return NextResponse.json({
      status: "error",
      message: "Eroare la verificarea statusului",
      error: error.message,
    })
  }
}
