import { Link, useLocation } from "react-router-dom"
import { useSelector } from "react-redux"
import type { RootState } from "@/store"
import { cn } from "@/lib/utils"
import {
  FileSignature,
  Database,
  ScanLine,
  Activity,
  Key,
  Cpu,
  Server,
} from "lucide-react"

const sidebarNavItems = [
  {
    title: "Smart Grid",
    href: "/devices",
    icon: <Cpu className="w-5 h-5 mr-3" />,
    roles: ["operator", "admin", "auditor", "OPERATOR", "ADMIN", "AUDITOR"],
  },
  {
    title: "Audit Ledger",
    href: "/ledger",
    icon: <Database className="w-5 h-5 mr-3" />,
    roles: ["admin", "auditor", "ADMIN", "AUDITOR"],
  },
  {
    title: "Air-Gapped Scanner",
    href: "/scan",
    icon: <ScanLine className="w-5 h-5 mr-3" />,
    roles: ["admin", "auditor", "ADMIN", "AUDITOR"],
  },
  {
    title: "SOC Threat Monitor",
    href: "/threats",
    icon: <Activity className="w-5 h-5 mr-3" />,
    roles: ["admin", "ADMIN"],
  },
  {
    title: "System Keys",
    href: "/keys",
    icon: <Key className="w-5 h-5 mr-3" />,
    roles: ["operator", "OPERATOR"],
  },
  {
    title: "Admin Dashboard",
    href: "/admin",
    icon: <Server className="w-5 h-5 mr-3" />,
    roles: ["admin", "ADMIN"],
  },
]

export function Sidebar() {
  const location = useLocation()
  const user = useSelector((state: RootState) => state.auth.user)

  // Filter items based on user role safely
  const visibleItems = sidebarNavItems.filter(item => 
    !item.roles || (user?.role && item.roles.includes(user.role))
  )

  return (
    <aside className="w-64 border-r bg-muted/20 hidden md:block min-h-[calc(100vh-4rem)]">
      <nav className="flex flex-col space-y-1 p-4">
        {visibleItems.map((item) => (
          <Link
            key={item.href}
            to={item.href}
            className={cn(
              "flex items-center px-4 py-3 rounded-md text-sm font-medium transition-colors hover:bg-accent hover:text-accent-foreground",
              location.pathname === item.href
                ? "bg-primary/10 text-primary hover:bg-primary/20"
                : "text-muted-foreground"
            )}
          >
            {item.icon}
            {item.title}
          </Link>
        ))}
      </nav>
    </aside>
  )
}
