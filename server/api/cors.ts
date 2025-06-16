import type { NextRequest, NextResponse } from "next/server"

export function cors(request: NextRequest, response: NextResponse) {
  // Obține originea din header-ul request-ului
  const origin = request.headers.get("origin") || "*"

  // Setează header-ele CORS
  response.headers.set("Access-Control-Allow-Origin", origin)
  response.headers.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
  response.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization")
  response.headers.set("Access-Control-Allow-Credentials", "true")

  return response
}
