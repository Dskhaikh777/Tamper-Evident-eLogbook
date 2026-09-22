import { useState, useEffect } from "react"
import { useSearchParams } from "react-router-dom"
import { LedgerTable } from "@/components/ledger/LedgerTable"
import { Button } from "@/components/ui/button"
import { useLazyVerifyLedgerQuery, useGetDevicesOverviewQuery } from "@/services/api/ledgerApi"
import { DatabaseZap, Loader2 } from "lucide-react"
import { toast } from "sonner"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"

export function LedgerViewPage() {
  const [searchParams] = useSearchParams()
  const [triggerVerify, { data: verifyData, isFetching }] = useLazyVerifyLedgerQuery()
  const { data: devices } = useGetDevicesOverviewQuery()
  
  const initialDevice = searchParams.get("device_id") || "ALL"
  const [selectedDevice, setSelectedDevice] = useState<string>(initialDevice)

  useEffect(() => {
    const urlDeviceId = searchParams.get("device_id")
    if (urlDeviceId) {
      setSelectedDevice(urlDeviceId)
    }
  }, [searchParams])

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
        <div className="flex items-center space-x-4">
          <Select value={selectedDevice} onValueChange={setSelectedDevice}>
            <SelectTrigger className="w-[220px]">
              <SelectValue placeholder="Filter by Device" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="ALL">All Devices</SelectItem>
              {devices?.map((device) => (
                <SelectItem key={device.id} value={device.id}>
                  {device.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>

          <Button 
            variant="outline" 
            onClick={handleGlobalVerify} 
            disabled={isFetching}
            className="border-emerald-500/50 hover:bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 whitespace-nowrap"
          >
            {isFetching ? (
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
            ) : (
              <DatabaseZap className="mr-2 h-4 w-4" />
            )}
            Run Global Integrity Check
          </Button>
        </div>
      </div>
      
      <LedgerTable verifyData={verifyData} selectedDeviceId={selectedDevice === "ALL" ? undefined : selectedDevice} />
    </div>
  )
}
