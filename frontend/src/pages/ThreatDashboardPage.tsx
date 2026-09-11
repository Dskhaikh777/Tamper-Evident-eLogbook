import { useFetchThreatStatusQuery, useTriggerHoneypotTrapMutation } from "@/services/api/ledgerApi"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Activity, ShieldAlert, ShieldCheck, AlertOctagon, Skull } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { Button } from "@/components/ui/button"
import { toast } from "sonner"

import { Skeleton } from "@/components/ui/skeleton"

export function ThreatDashboardPage() {
  // Polling interval is handled by configuring the hook
  const { data: threatData, isLoading, error } = useFetchThreatStatusQuery(undefined, {
    pollingInterval: 5000, // Poll every 5s
  })

  const [triggerHoneypot, { isLoading: isAttacking }] = useTriggerHoneypotTrapMutation()

  const handleSimulateAttack = async () => {
    try {
      await triggerHoneypot().unwrap()
      toast("Hostile Probe Sent", {
        description: "A simulated attack request was sent to the honeypot endpoints.",
        duration: 3000,
        icon: <Skull className="h-4 w-4 text-destructive" />
      })
    } catch (err) {
      toast.error("Failed to simulate attack", {
        description: "Could not reach the honeypot endpoint."
      })
    }
  }

  if (isLoading && !threatData) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 border-b pb-6 gap-4">
          <div>
            <Skeleton className="h-10 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
          <Skeleton className="h-24 w-full md:w-64 rounded-xl" />
        </div>
        <Skeleton className="h-12 w-full rounded-lg" />
        <div className="mt-8">
          <Skeleton className="h-8 w-64 mb-4" />
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <Skeleton key={i} className="h-24 w-full rounded-xl" />
            ))}
          </div>
        </div>
      </div>
    )
  }

  if (error || !threatData) {
    return (
      <Card className="border-destructive max-w-3xl mx-auto mt-12">
        <CardContent className="flex flex-col justify-center items-center h-64 text-center">
          <ShieldAlert className="h-12 w-12 text-destructive mb-4" />
          <h2 className="text-xl font-bold">SOC Telemetry Offline</h2>
          <p className="text-muted-foreground">Unable to connect to the threat monitoring feed.</p>
        </CardContent>
      </Card>
    )
  }

  const isCritical = threatData.status === "critical"

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between mb-8 border-b pb-6 gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight flex items-center gap-2">
            <Activity className="h-8 w-8 text-blue-500" />
            SOC Threat Dashboard
          </h1>
          <p className="text-muted-foreground text-sm mt-1">
            Real-time monitoring of deployed honey-tokens and decoy nodes.
          </p>
          <Button 
            variant="outline" 
            size="sm"
            onClick={handleSimulateAttack}
            disabled={isAttacking}
            className="mt-4 border-destructive/50 text-destructive hover:bg-destructive/10"
          >
            <Skull className={`mr-2 h-4 w-4 ${isAttacking ? 'animate-pulse' : ''}`} />
            Simulate Hostile Intrusion
          </Button>
        </div>
        
        <Card className={`w-full md:w-auto border-2 ${isCritical ? 'border-destructive' : 'border-emerald-500'}`}>
          <CardContent className="p-4 flex items-center gap-4">
            {isCritical ? (
              <AlertOctagon className="h-10 w-10 text-destructive animate-pulse" />
            ) : (
              <ShieldCheck className="h-10 w-10 text-emerald-500" />
            )}
            <div>
              <p className="text-xs font-semibold uppercase text-muted-foreground">System Status</p>
              <h3 className={`text-xl font-bold ${isCritical ? 'text-destructive' : 'text-emerald-500'}`}>
                {isCritical ? 'CRITICAL BREACH' : 'SECURE'}
              </h3>
            </div>
            <div className="ml-4 pl-4 border-l">
              <p className="text-xs font-semibold uppercase text-muted-foreground">Integrity</p>
              <h3 className="text-xl font-bold">{threatData.integrity}</h3>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="bg-muted/30 p-4 rounded-lg text-sm border font-mono">
        {threatData.message}
      </div>

      {isCritical && "breached_nodes" in threatData && threatData.breached_nodes.length > 0 && (
        <div className="mt-8">
          <h3 className="text-xl font-semibold mb-4 flex items-center gap-2 text-destructive">
            <ShieldAlert className="h-5 w-5" />
            Compromised Nodes Detected
          </h3>
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
            {threatData.breached_nodes.map((node) => (
              <Card key={node.id} className="border-destructive/50 bg-destructive/5">
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-lg font-bold font-mono">{node.decoy_name}</CardTitle>
                    <Badge variant="destructive" className="animate-pulse">BREACH DETECTED</Badge>
                  </div>
                  <CardDescription>Decoy ID: #{node.id}</CardDescription>
                </CardHeader>
                <CardContent className="pb-2 space-y-2">
                  <div className="flex justify-between border-b pb-2">
                    <span className="text-sm text-muted-foreground">Probes Blocked:</span>
                    <span className="font-bold text-destructive">{node.accessed_count}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-sm text-muted-foreground">Last Activity:</span>
                    <span className="text-sm font-medium">
                      {node.last_breach_timestamp 
                        ? formatDistanceToNow(new Date(node.last_breach_timestamp), { addSuffix: true }) 
                        : "Unknown"}
                    </span>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}

      {/* If secure, we can show a placeholder grid of protected honey-tokens */}
      {!isCritical && (
        <div className="mt-8">
          <h3 className="text-xl font-semibold mb-4">Active Defensive Grid</h3>
          <div className="grid gap-4 md:grid-cols-3 lg:grid-cols-4">
            {[1, 2, 3, 4].map((i) => (
              <Card key={i} className="border-emerald-500/20 bg-emerald-500/5">
                <CardHeader className="p-4 pb-2">
                  <div className="flex justify-between items-center">
                    <CardTitle className="text-sm font-bold text-emerald-700 dark:text-emerald-400">Node Alpha-{i}</CardTitle>
                    <ShieldCheck className="h-4 w-4 text-emerald-500" />
                  </div>
                </CardHeader>
                <CardContent className="p-4 pt-2">
                  <Badge variant="outline" className="bg-emerald-500/10 text-emerald-600 border-emerald-500/30 text-[10px]">
                    SECURE
                  </Badge>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
