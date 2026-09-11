import { Link, useLocation } from "react-router-dom"
import { cn } from "@/lib/utils"
import {
  FileSignature,
  Database,
  ScanLine,
  Activity,
  Key,
} from "lucide-react"

const sidebarNavItems = [
  {
    title: "Operator Entry",
    href: "/entry",
    icon: <FileSignature className="w-5 h-5 mr-3" />,
  },
  {
    title: "Audit Ledger",
    href: "/ledger",
    icon: <Database className="w-5 h-5 mr-3" />,
  },
  {
    title: "Air-Gapped Scanner",
    href: "/scan",
    icon: <ScanLine className="w-5 h-5 mr-3" />,
  },
  {
    title: "SOC Threat Monitor",
    href: "/threats",
    icon: <Activity className="w-5 h-5 mr-3" />,
  },
  {
    title: "System Keys",
    href: "/keys",
    icon: <Key className="w-5 h-5 mr-3" />,
  },
]

export function Sidebar() {
  const location = useLocation()

  return (
    <aside className="w-64 border-r bg-muted/20 hidden md:block min-h-[calc(100vh-4rem)]">
      <nav className="flex flex-col space-y-1 p-4">
        {sidebarNavItems.map((item) => (
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
