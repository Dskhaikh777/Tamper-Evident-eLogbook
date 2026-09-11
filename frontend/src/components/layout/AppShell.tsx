import { Outlet } from "react-router-dom"
import { Header } from "./Header"
import { Sidebar } from "./Sidebar"

export function AppShell() {
  return (
    <div className="relative flex min-h-screen flex-col bg-background">
      <Header />
      <div className="flex flex-1">
        <Sidebar />
        <main className="flex-1 overflow-y-auto bg-slate-50/50 dark:bg-zinc-950/50 p-6 md:p-8">
          <div className="mx-auto max-w-5xl">
            <Outlet />
          </div>
        </main>
      </div>
    </div>
  )
}
