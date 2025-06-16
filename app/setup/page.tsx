"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { AlertCircle, CheckCircle2, Database, Loader2 } from "lucide-react"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"

export default function SetupPage() {
  const [dbPath, setDbPath] = useState("/data/ads/ads_database.db")
  const [status, setStatus] = useState<"idle" | "loading" | "success" | "error">("idle")
  const [message, setMessage] = useState("")

  const initializeDatabase = async () => {
    try {
      setStatus("loading")
      setMessage("Inițializare bază de date...")

      const response = await fetch("/api/setup", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ dbPath }),
      })

      const data = await response.json()

      if (response.ok) {
        setStatus("success")
        setMessage(data.message || "Baza de date a fost inițializată cu succes!")
      } else {
        setStatus("error")
        setMessage(data.error || "A apărut o eroare la inițializarea bazei de date.")
      }
    } catch (error) {
      setStatus("error")
      setMessage(`Eroare: ${error.message}`)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50 p-6 flex items-center justify-center">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle className="text-2xl">Configurare AiReclame</CardTitle>
          <CardDescription>Inițializează baza de date pentru sistemul de crawling</CardDescription>
        </CardHeader>
        <CardContent className="space-y-6">
          <div className="space-y-2">
            <Label htmlFor="dbPath">Calea către baza de date SQLite</Label>
            <Input
              id="dbPath"
              value={dbPath}
              onChange={(e) => setDbPath(e.target.value)}
              placeholder="/path/to/database.db"
            />
            <p className="text-sm text-muted-foreground">
              Asigură-te că directorul există și are permisiuni de scriere
            </p>
          </div>

          {status === "success" && (
            <Alert variant="default" className="bg-green-50 border-green-200">
              <CheckCircle2 className="h-4 w-4 text-green-600" />
              <AlertTitle>Succes</AlertTitle>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          )}

          {status === "error" && (
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>Eroare</AlertTitle>
              <AlertDescription>{message}</AlertDescription>
            </Alert>
          )}
        </CardContent>
        <CardFooter>
          <Button onClick={initializeDatabase} disabled={status === "loading" || !dbPath} className="w-full">
            {status === "loading" ? (
              <>
                <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                Se inițializează...
              </>
            ) : (
              <>
                <Database className="mr-2 h-4 w-4" />
                Inițializează baza de date
              </>
            )}
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
