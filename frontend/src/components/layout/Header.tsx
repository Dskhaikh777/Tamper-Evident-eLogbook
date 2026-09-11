import { useDispatch, useSelector } from "react-redux"
import { ShieldCheck, LogOut, User } from "lucide-react"
import { ThemeToggle } from "@/components/theme/ThemeToggle"
import { Badge } from "@/components/ui/badge"
import type { RootState } from "@/store"
import { logout } from "@/store/slices/authSlice"
import { Button } from "@/components/ui/button"

export function Header() {
  const dispatch = useDispatch()
  const { user } = useSelector((state: RootState) => state.auth)

  const handleSignOut = () => {
    dispatch(logout())
  }

  return (
    <header className="sticky top-0 z-50 w-full border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60">
      <div className="container flex h-14 items-center justify-between mx-auto px-4">
        <div className="flex items-center gap-2">
          <ShieldCheck className="h-6 w-6 text-emerald-600 dark:text-emerald-500" aria-hidden="true" />
          <span className="hidden sm:inline-block font-bold tracking-tight">
            Tamper-Evident E-Logbook with Air-Gapped QR Verification
          </span>
          <span className="sm:hidden font-bold tracking-tight">
            E-Logbook
          </span>
        </div>

        <div className="flex flex-1 items-center justify-end gap-4">
          <div className="flex items-center gap-2">
            {user ? (
              <>
                <Badge variant="outline" className="hidden sm:flex items-center gap-1 uppercase">
                  <span className="h-2 w-2 rounded-full bg-emerald-500" aria-hidden="true"></span>
                  <span>{user.role}</span>
                </Badge>
                
                <Button variant="ghost" size="sm" onClick={handleSignOut} className="text-muted-foreground hover:text-destructive">
                  <LogOut className="h-4 w-4 mr-2" aria-hidden="true" />
                  <span className="hidden sm:inline-block">Sign Out</span>
                </Button>
              </>
            ) : (
              <Button variant="ghost" size="sm" disabled>
                <User className="h-4 w-4 mr-2" aria-hidden="true" />
                Guest
              </Button>
            )}
          </div>
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
