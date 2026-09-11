import { useFetchLogsQuery } from "@/services/api/ledgerApi"
import type { LogEntryResponse } from "@/services/api/ledgerApi"
import { createCanonicalPayload, verifySignature } from "@/lib/crypto"
import { toast } from "sonner"
import { format } from "date-fns"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { ShieldCheck, ShieldAlert, KeyRound, Loader2 } from "lucide-react"
import { useState } from "react"
import { QRCodeGenerator } from "@/components/qr/QRCodeGenerator"

import { Skeleton } from "@/components/ui/skeleton"
import type { LedgerVerificationResult } from "@/services/api/ledgerApi"

export function LedgerTable({ verifyData }: { verifyData?: LedgerVerificationResult }) {
  const { data: logs, isLoading, error } = useFetchLogsQuery()
  const [verifyingId, setVerifyingId] = useState<string | null>(null)

  const handleVerify = async (log: LogEntryResponse) => {
    try {
      setVerifyingId(log.id)
      
      const canonicalPayload = createCanonicalPayload({
        operator_id: log.operator_id,
        action_type: log.action_type,
        data_payload: log.data_payload,
      })

      const isValid = await verifySignature(canonicalPayload, log.signature, log.public_key)

      if (isValid) {
        toast.success("Signature Verified", {
          description: "The cryptographic signature matches the public key and payload.",
          duration: 8000,
        })
      } else {
        toast.error("Signature Invalid", {
          description: "The signature failed mathematical verification. Payload may be tampered.",
          duration: 8000,
        })
      }
    } catch (err) {
      toast.error("Verification Error", {
        description: "An error occurred during verification.",
        duration: 8000,
      })
    } finally {
      setVerifyingId(null)
    }
  }

  if (isLoading) {
    return (
      <Card className="border-emerald-500/20 shadow-md">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-muted-foreground">
            <Skeleton className="h-6 w-6 rounded-full" />
            <Skeleton className="h-6 w-48" />
          </CardTitle>
          <Skeleton className="h-4 w-72 mt-2" />
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <Skeleton className="h-10 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
            <Skeleton className="h-12 w-full" />
          </div>
        </CardContent>
      </Card>
    )
  }

  if (error || !logs) {
    return (
      <Card className="border-destructive">
        <CardContent className="flex flex-col justify-center items-center h-64 text-center">
          <ShieldAlert className="h-12 w-12 text-destructive mb-4" />
          <h2 className="text-xl font-bold">Failed to load ledger</h2>
          <p className="text-muted-foreground">Unable to fetch the immutable audit trail.</p>
        </CardContent>
      </Card>
    )
  }

  const isGloballyVerified = verifyData?.status === "valid"
  const GENESIS_HASH = "0".repeat(64)

  return (
    <Card className="border-emerald-500/20 shadow-md">
      <CardHeader>
        <CardTitle className="text-emerald-700 dark:text-emerald-500 flex items-center gap-2">
          <ShieldCheck className="h-6 w-6" />
          Immutable Audit Ledger
        </CardTitle>
        <CardDescription>
          Cryptographically chained records. Hashes are linked to guarantee non-repudiation.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div className="rounded-md border">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead>Timestamp</TableHead>
                <TableHead>Operator</TableHead>
                <TableHead>Action</TableHead>
                <TableHead>Payload</TableHead>
                <TableHead>Hash Chain</TableHead>
                <TableHead className="text-right">Actions</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {logs.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} className="text-center py-8 text-muted-foreground">
                    No log entries found.
                  </TableCell>
                </TableRow>
              ) : (
                logs.map((log, index) => {
                  // Verify chain link visually
                  const prevLog = index > 0 ? logs[index - 1] : null
                  const isChainedCorrectly = prevLog ? log.previous_hash === prevLog.current_hash : log.previous_hash === GENESIS_HASH
                  
                  const isTampered = verifyData?.status === "tampered" && verifyData.tampered_block_id === Number(log.id)
                  const showVerified = isGloballyVerified && isChainedCorrectly

                  return (
                    <TableRow key={log.id}>
                      <TableCell className="whitespace-nowrap">
                        {format(new Date(log.timestamp), "yyyy-MM-dd HH:mm:ss")}
                      </TableCell>
                      <TableCell className="font-medium">{log.operator_id}</TableCell>
                      <TableCell>
                        <Badge variant="outline">{log.action_type}</Badge>
                      </TableCell>
                      <TableCell className="max-w-[200px] truncate" title={log.data_payload}>
                        <code className="text-xs">{log.data_payload}</code>
                      </TableCell>
                      <TableCell>
                        <div className="flex flex-col space-y-1">
                          <code className="text-xs truncate max-w-[120px]" title={log.current_hash}>
                            {log.current_hash}
                          </code>
                          <Badge 
                            variant={showVerified ? "default" : isChainedCorrectly && !isTampered ? "secondary" : "destructive"}
                            className={
                              showVerified 
                                ? "bg-emerald-500/10 text-emerald-600 hover:bg-emerald-500/20 text-[10px] h-4 px-1" 
                                : isChainedCorrectly && !isTampered 
                                  ? "text-[10px] h-4 px-1" 
                                  : "text-[10px] h-4 px-1 bg-destructive"
                            }
                          >
                            {showVerified ? "VERIFIED" : isChainedCorrectly && !isTampered ? "CHAIN OK" : "BROKEN CHAIN"}
                          </Badge>
                        </div>
                      </TableCell>
                      <TableCell className="text-right space-x-2">
                        <QRCodeGenerator log={log} />
                        <Button 
                          variant="ghost" 
                          size="sm" 
                          onClick={() => handleVerify(log)}
                          disabled={verifyingId === log.id}
                        >
                          {verifyingId === log.id ? (
                            <Loader2 className="h-4 w-4 animate-spin" />
                          ) : (
                            <KeyRound className="h-4 w-4 mr-2" />
                          )}
                          Verify
                        </Button>
                      </TableCell>
                    </TableRow>
                  )
                })
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>
  )
}
