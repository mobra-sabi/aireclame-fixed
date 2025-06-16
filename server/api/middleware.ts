import { type NextRequest, NextResponse } from "next/server"

export function middleware(request: NextRequest) {
  // Obține originea din header-ul request-ului
  const origin = request.headers.get("origin") || "*"

  // Verifică dacă este un request OPTIONS (preflight)
  if (request.method === "OPTIONS") {
    // Creează un răspuns nou
    const response = new NextResponse(null, { status: 200 })

    // Setează header-ele CORS
    response.headers.set("Access-Control-Allow-Origin", origin)
    response.headers.set("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
    response.headers.set("Access-Control-Allow-Headers", "Content-Type, Authorization")
    response.headers.set("Access-Control-Allow-Credentials", "true")

    return response
  }

  // Pentru alte tipuri de request-uri, continuă cu procesarea normală
  return NextResponse.next()
}

export const config = {
  matcher: "/api/:path*",
}
