import { useState } from "react"
import { useNavigate } from "react-router-dom"
import { useDispatch } from "react-redux"
import { loginSuccess } from "@/store/slices/authSlice"
import type { Role } from "@/store/slices/authSlice"
import { axiosClient } from "@/services/api/axiosClient"
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { ShieldAlert, Loader2, Database } from "lucide-react"
import { toast } from "sonner"

export function LoginPage() {
  const [username, setUsername] = useState("")
  const [password, setPassword] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const [isSeeding, setIsSeeding] = useState(false)
  const dispatch = useDispatch()
  const navigate = useNavigate()

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)

    try {
      const params = new URLSearchParams()
      params.append("username", username)
      params.append("password", password)

      const response = await axiosClient.post("/auth/token", params, {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      })

      const { access_token, role, employee_id } = response.data

      // Dispatch to Redux
      dispatch(
        loginSuccess({
          user: {
            id: employee_id,
            name: username.charAt(0).toUpperCase() + username.slice(1),
            role: role.toUpperCase() as Role,
          },
          accessToken: access_token,
        })
      )

      toast.success("Login Successful", {
        description: `Welcome back, ${username}. Access level: ${role.toUpperCase()}`,
      })

      navigate("/keys")
    } catch (err: any) {
      toast.error("Authentication Failed", {
        description: err.response?.data?.detail || "Invalid credentials or network error.",
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleSeedDatabase = async () => {
    setIsSeeding(true)
    try {
      const response = await axiosClient.post("/auth/setup-users")
      toast.success("Database Seeded", {
        description: response.data.message || "Default users provisioned successfully.",
      })
    } catch (err: any) {
      toast.error("Seeding Failed", {
        description: err.response?.data?.detail || "Could not setup default users.",
      })
    } finally {
      setIsSeeding(false)
    }
  }

  return (
    <div className="flex flex-col min-h-screen items-center justify-center p-4 bg-muted/30">
      <div className="mb-8 flex flex-col items-center">
        <div className="rounded-full bg-emerald-500/10 p-4 mb-4">
          <ShieldAlert className="h-12 w-12 text-emerald-600" />
        </div>
        <h1 className="text-3xl font-bold tracking-tight">Tamper-Evident eLogbook</h1>
        <p className="text-muted-foreground mt-2">Restricted Access. Authentication Required.</p>
      </div>

      <Card className="w-full max-w-md shadow-lg border-emerald-500/20">
        <CardHeader>
          <CardTitle>System Login</CardTitle>
          <CardDescription>
            Enter your operator or administrative credentials.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                placeholder="operator"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="operator@secure123"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isLoading ? "Authenticating..." : "Login to System"}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="flex flex-col border-t bg-muted/50 py-4 gap-4">
          <p className="text-xs text-center text-muted-foreground">
            Development Mode Utility
          </p>
          <Button
            variant="outline"
            size="sm"
            onClick={handleSeedDatabase}
            disabled={isSeeding}
            className="w-full text-xs"
          >
            {isSeeding ? (
              <Loader2 className="mr-2 h-3 w-3 animate-spin" />
            ) : (
              <Database className="mr-2 h-3 w-3" />
            )}
            Seed Database Defaults
          </Button>
        </CardFooter>
      </Card>
    </div>
  )
}
