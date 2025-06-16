import { NextResponse } from "next/server"

export async function GET() {
  try {
    // Simulează statusul analizei
    const isRunning = Math.random() > 0.7 // 30% chance it's running

    if (isRunning) {
      return NextResponse.json({
        status: "running",
        progress: Math.floor(Math.random() * 80) + 10, // 10-90%
        current_phase: "Analyzing video content",
        stats: {
          videos_found: Math.floor(Math.random() * 5000) + 1000,
          ads_detected: Math.floor(Math.random() * 1500) + 200,
          errors: Math.floor(Math.random() * 50),
          api_calls: Math.floor(Math.random() * 2000) + 500,
          elapsed_time: Math.floor(Math.random() * 7200) + 300, // seconds
        },
        message: "Analysis in progress. Processing YouTube videos from 2025...",
      })
    } else {
      return NextResponse.json({
        status: "idle",
        progress: 0,
        current_phase: "Ready to start",
        stats: {
          videos_found: 0,
          ads_detected: 0,
          errors: 0,
          api_calls: 0,
          elapsed_time: 0,
        },
        message: "Click Start Analysis to begin comprehensive 2025 YouTube ads analysis",
      })
    }
  } catch (error) {
    console.error("Error checking analysis status:", error)
    return NextResponse.json(
      {
        status: "error",
        message: "Error checking analysis status",
        error: error.message,
      },
      { status: 500 },
    )
  }
}
