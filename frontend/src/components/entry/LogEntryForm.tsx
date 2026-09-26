import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { useSelector } from "react-redux"
import type { RootState } from "@/store"
import { useCreateLogMutation } from "@/services/api/ledgerApi"
import { createCanonicalPayload, signPayload } from "@/lib/crypto"
import { toast } from "sonner"
import { Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

const logEntrySchema = z.object({
  action_type: z.enum(["TEMPERATURE_CHECK", "BATCH_MIXING", "CALIBRATION", "CLEANING", "MAINTENANCE"], {
    message: "Please select an action type.",
  }),
  data_payload: z.string().min(10, {
    message: "Data payload must be at least 10 characters.",
  }).refine((val) => {
    try {
      JSON.parse(val)
      return true
    } catch (e) {
      // Allow unstructured text if not JSON, but backend might strictly want JSON. 
      // User directive: "Must be a valid JSON string or structured text detailing the log metrics."
      return true
    }
  }, "Payload should be structured text or valid JSON."),
})

export function LogEntryForm({ deviceId }: { deviceId?: string }) {
  const { user, keyPair } = useSelector((state: RootState) => state.auth)
  const [createLog, { isLoading }] = useCreateLogMutation()
  const [isSigning, setIsSigning] = useState(false)

  const form = useForm<z.infer<typeof logEntrySchema>>({
    resolver: zodResolver(logEntrySchema),
    defaultValues: {
      action_type: undefined,
      data_payload: "",
    },
  })

  // Block submission if no keys exist
  if (!user || !keyPair) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Cryptographic Identity Missing</CardTitle>
          <CardDescription>
            You must have an active cryptographic identity to sign ledger entries.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Button variant="destructive" onClick={() => window.location.href = '/keys'}>
            Generate Keypair
          </Button>
        </CardContent>
      </Card>
    )
  }

  async function onSubmit(values: z.infer<typeof logEntrySchema>) {
    if (!deviceId) {
      toast.error("Device Context Missing", {
        description: "Cannot append log without a target device UUID.",
      })
      return
    }

    try {
      setIsSigning(true)

      // 1. Construct the payload
      const canonicalPayload = createCanonicalPayload({
        operator_id: user!.id,
        action_type: values.action_type,
        data_payload: values.data_payload,
      })

      // 2. Await signPayload to generate the Ed25519 signature
      const signature = await signPayload(canonicalPayload, keyPair!.privateKey)

      // 3. Dispatch the createLog mutation
      await createLog({
        device_id: deviceId,
        operator_id: user!.id,
        action_type: values.action_type,
        data_payload: values.data_payload,
        signature,
        public_key: keyPair!.publicKey,
        raw_payload: canonicalPayload,
      }).unwrap()

      toast.success("Cryptographic Log Appended to Ledger", {
        description: `Signature: ${signature.substring(0, 16)}...`,
        duration: 8000,
      })
      
      form.reset()
    } catch (error: any) {
      console.error(error)
      toast.error("Signature Validation Failed / Network Error", {
        description: error?.data?.detail || error.message || "Failed to append log entry.",
        duration: 8000,
      })
    } finally {
      setIsSigning(false)
    }
  }

  return (
    <Card className="border-emerald-500/20 shadow-md">
      <CardHeader>
        <CardTitle className="text-2xl text-emerald-700 dark:text-emerald-500">Record Data Entry</CardTitle>
        <CardDescription>
          Cryptographically sign and append a new immutable entry to the ledger.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <Form {...form}>
          <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
            <FormField
              control={form.control}
              name="action_type"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Action Type</FormLabel>
                  <Select onValueChange={field.onChange} defaultValue={field.value}>
                    <FormControl>
                      <SelectTrigger>
                        <SelectValue placeholder="Select an action type" />
                      </SelectTrigger>
                    </FormControl>
                    <SelectContent>
                      <SelectItem value="TEMPERATURE_CHECK">Temperature Check</SelectItem>
                      <SelectItem value="BATCH_MIXING">Batch Mixing</SelectItem>
                      <SelectItem value="CALIBRATION">Calibration</SelectItem>
                      <SelectItem value="CLEANING">Cleaning</SelectItem>
                      <SelectItem value="MAINTENANCE">Maintenance</SelectItem>
                    </SelectContent>
                  </Select>
                  <FormDescription>
                    The category of the operation performed.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <FormField
              control={form.control}
              name="data_payload"
              render={({ field }) => (
                <FormItem>
                  <FormLabel>Data Payload</FormLabel>
                  <FormControl>
                    <Textarea
                      placeholder='{"temperature": 4.2, "unit": "C"}'
                      className="font-mono min-h-[120px]"
                      {...field}
                    />
                  </FormControl>
                  <FormDescription>
                    Enter the metrics or log data as structured text or valid JSON.
                  </FormDescription>
                  <FormMessage />
                </FormItem>
              )}
            />

            <Button type="submit" disabled={isLoading || isSigning} className="w-full bg-emerald-600 hover:bg-emerald-700 text-white">
              {(isLoading || isSigning) && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
              {isSigning ? "Signing Payload..." : isLoading ? "Appending to Ledger..." : "Sign & Submit Log Entry"}
            </Button>
          </form>
        </Form>
      </CardContent>
    </Card>
  )
}
