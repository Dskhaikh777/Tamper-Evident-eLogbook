import { LogEntryForm } from "@/components/entry/LogEntryForm"
import { ShieldCheck } from "lucide-react"

export function NewLogEntryPage() {
  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center space-x-3 mb-8 border-b pb-4">
        <div className="bg-emerald-100 dark:bg-emerald-900/30 p-2 rounded-full">
          <ShieldCheck className="w-6 h-6 text-emerald-600 dark:text-emerald-400" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">New Tamper-Evident Record</h1>
          <p className="text-muted-foreground text-sm">
            Data entered here will be cryptographically signed and permanently appended to the ledger.
          </p>
        </div>
      </div>
      
      <LogEntryForm />
    </div>
  )
}
