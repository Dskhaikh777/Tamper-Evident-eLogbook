import { Navigate, Outlet } from "react-router-dom"
import { useSelector } from "react-redux"
import type { RootState } from "@/store"
import type { Role } from "@/store/slices/authSlice"
import { ShieldAlert } from "lucide-react"
import { Button } from "@/components/ui/button"
import { Link } from "react-router-dom"

interface ProtectedRouteProps {
  allowedRoles: Role[]
}

export function ProtectedRoute({ allowedRoles }: ProtectedRouteProps) {
  const { user, isAuthenticated } = useSelector((state: RootState) => state.auth)

  if (!isAuthenticated || !user) {
    return <Navigate to="/login" replace />
  }

  if (!allowedRoles.includes(user.role)) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center px-4 animate-in fade-in zoom-in-95 duration-500">
        <ShieldAlert className="w-16 h-16 text-destructive mb-6" aria-hidden="true" />
        <h1 className="text-3xl font-bold tracking-tight mb-2">403 Unauthorized Access</h1>
        <p className="text-muted-foreground max-w-md mb-8">
          Role Clearance Required. Your current role ({user.role}) does not have permission to view this section.
        </p>
        <Button asChild>
          <Link to="/">Return to Dashboard</Link>
        </Button>
      </div>
    )
  }

  return <Outlet />
}
