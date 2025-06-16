import type React from "react"
import "./globals.css"
import { Inter } from "next/font/google"

const inter = Inter({ subsets: ["latin"] })

export const metadata = {
  title: "AireClame - Platformă de analiză a reclamelor YouTube",
  description: "Sistem avansat de crawling și analiză a reclamelor YouTube folosind AI și multiple GPU-uri",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ro">
      <body className={inter.className}>{children}</body>
    </html>
  )
}
