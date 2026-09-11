import { LedgerTable } from "@/components/ledger/LedgerTable"
import { Button } from "@/components/ui/button"
import { useLazyVerifyLedgerQuery } from "@/services/api/ledgerApi"
import { DatabaseZap, Loader2 } from "lucide-react"
import { toast } from "sonner"

export function LedgerViewPage() {
  const [triggerVerify, { data: verifyData, isFetching }] = useLazyVerifyLedgerQuery()

  const handleGlobalVerify = async () => {
    try {
      const result = await triggerVerify().unwrap()
      if (result.status === "valid") {
        toast.success("Ledger Integrity Verified", {
          description: result.message,
          duration: 8000,
        })
      } else {
        toast.error("Tamper Evidence Detected!", {
          description: result.message,
          duration: 10000,
        })
      }
    } catch (error) {
      toast.error("Verification Failed", {
        description: "An error occurred while connecting to the validation engine.",
      })
    }
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between mb-8 border-b pb-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Ledger Operations</h1>
          <p className="text-muted-foreground text-sm mt-1">
            Auditor & Admin view for cryptographically signed records.
          </p>
        </div>
        <Button 
          variant="outline" 
          onClick={handleGlobalVerify} 
          disabled={isFetching}
          className="border-emerald-500/50 hover:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400"
        >
          {isFetching ? (
            <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          ) : (
            <DatabaseZap className="mr-2 h-4 w-4" />
          )}
          Run Global Integrity Check
        </Button>
      </div>
      
      <LedgerTable verifyData={verifyData} />
    </div>
  )
}
