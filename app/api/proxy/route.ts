import { type NextRequest, NextResponse } from "next/server"

// Acest API va acționa ca un proxy pentru serverul tău
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const endpoint = searchParams.get("endpoint")

  if (!endpoint) {
    return NextResponse.json({ error: "Endpoint parameter is required" }, { status: 400 })
  }

  try {
    const apiUrl = `${process.env.API_URL || "http://100.111.7.74"}/api/${endpoint}`
    const response = await fetch(apiUrl)
    const data = await response.json()

    return NextResponse.json(data)
  } catch (error) {
    console.error("Error proxying request:", error)
    return NextResponse.json({ error: "Failed to fetch data from server" }, { status: 500 })
  }
}
