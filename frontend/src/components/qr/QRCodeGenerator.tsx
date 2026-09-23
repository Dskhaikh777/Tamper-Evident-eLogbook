import { QRCodeCanvas } from "qrcode.react"
import type { LogEntryResponse } from "@/services/api/ledgerApi"
import { Button } from "@/components/ui/button"
import { QrCode, Download } from "lucide-react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog"
import { useRef } from "react"

interface QRCodeGeneratorProps {
  log: LogEntryResponse
}

export function QRCodeGenerator({ log }: QRCodeGeneratorProps) {
  const qrRef = useRef<HTMLDivElement>(null)

  // Serialize the essential data into a compact JSON string
  const qrPayload = JSON.stringify({
    o: log.operator_employee_id,
    a: log.action_type,
    d: log.data_payload,
    s: log.signature,
    p: log.public_key,
  })

  const downloadQR = () => {
    if (!qrRef.current) return
    const canvas = qrRef.current.querySelector("canvas")
    if (!canvas) return
    
    const url = canvas.toDataURL("image/png")
    const link = document.createElement("a")
    link.href = url
    link.download = `log-qr-${log.id}.png`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
  }

  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="outline" size="sm">
          <QrCode className="h-4 w-4 mr-2" />
          QR
        </Button>
      </DialogTrigger>
      <DialogContent className="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Air-Gapped Verification QR</DialogTitle>
          <DialogDescription>
            Scan this code with the offline verification module to authenticate this record's signature mathematically.
          </DialogDescription>
        </DialogHeader>
        
        <div className="flex flex-col items-center justify-center p-6 space-y-6">
          <div className="bg-white p-4 rounded-xl shadow-sm border" ref={qrRef}>
            <QRCodeCanvas 
              value={qrPayload} 
              size={256}
              level={"M"}
              includeMargin={true}
              fgColor="#000000"
              bgColor="#ffffff"
            />
          </div>
          <div className="text-sm text-center text-muted-foreground break-all max-w-[300px]">
            Payload contains cryptographic signature and public key.
          </div>
        </div>

        <div className="flex justify-end pt-4 border-t">
          <Button onClick={downloadQR} className="w-full">
            <Download className="h-4 w-4 mr-2" />
            Download QR Code
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}
