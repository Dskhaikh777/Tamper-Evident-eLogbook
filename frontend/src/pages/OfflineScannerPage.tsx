import { useEffect, useState, useRef } from "react"
import { useNavigate } from "react-router-dom"
import { Html5Qrcode } from "html5-qrcode"
import { createCanonicalPayload, verifySignature } from "@/lib/crypto"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { ScanLine, ShieldCheck, ShieldAlert, WifiOff, Loader2 } from "lucide-react"

interface ScannedPayload {
  o: string // operator_id
  a: string // action_type
  d: string // data_payload
  s: string // signature
  p: string // public_key
}

export function OfflineScannerPage() {
  const [scanResult, setScanResult] = useState<ScannedPayload | null>(null)
  const [verificationResult, setVerificationResult] = useState<"verified" | "failed" | null>(null)
  const [scannerActive, setScannerActive] = useState(true)
  const [isStartingCamera, setIsStartingCamera] = useState(false)
  const [cameraError, setCameraError] = useState<string | null>(null)
  
  const isInitializing = useRef<boolean>(false)

  useEffect(() => {
    if (!scannerActive || isInitializing.current) return

    let html5QrCode: Html5Qrcode | null = null
    let isMounted = true

    const startScanner = async () => {
      isInitializing.current = true
      setIsStartingCamera(true)
      setCameraError(null)

      // Ensure the DOM element is actually available
      const element = document.getElementById("qr-reader")
      if (!element) {
        if (isMounted) setIsStartingCamera(false)
        isInitializing.current = false
        return
      }

      try {
        html5QrCode = new Html5Qrcode("qr-reader")
        
        const config = { fps: 10, qrbox: { width: 250, height: 250 } }
        const onScanSuccess = (decodedText: string) => {
          if (html5QrCode?.isScanning) {
            html5QrCode.stop().then(() => {
              if (isMounted) {
                setScannerActive(false)
                processScannedText(decodedText)
              }
            }).catch(console.error)
          }
        }
        const onScanFailure = () => {
          // Ignore continuous scan parse errors
        }

        try {
          // First try rear/environment camera
          await html5QrCode.start({ facingMode: "environment" }, config, onScanSuccess, onScanFailure)
        } catch (envError) {
          console.warn("Environment camera not found, falling back to default/user camera.", envError)
          // Fallback to any available camera (usually laptop webcam)
          await html5QrCode.start({ facingMode: "user" }, config, onScanSuccess, onScanFailure)
        }
        
      } catch (err: any) {
        if (isMounted) {
          setCameraError(err?.message || "Failed to access camera. Please ensure permissions are granted.")
        }
      } finally {
        if (isMounted) {
          setIsStartingCamera(false)
        }
        // Keep isInitializing true while active to prevent overlapping mounts
      }
    }

    startScanner()

    return () => {
      isMounted = false
      isInitializing.current = false
      
      const destroyScanner = async () => {
        try {
          if (html5QrCode && html5QrCode.isScanning) {
            await html5QrCode.stop()
          }
          if (html5QrCode) {
            html5QrCode.clear()
          }
        } catch (error) {
          console.error("Cleanup error", error)
        } finally {
          // Hard DOM wipe as a failsafe against strict mode residue
          const element = document.getElementById("qr-reader")
          if (element) {
            element.innerHTML = ""
          }
        }
      }
      
      destroyScanner()
    }
  }, [scannerActive])

  const navigate = useNavigate()

  function processScannedText(decodedText: string) {
    try {
      const payload = JSON.parse(decodedText)
      
      if (payload.type === "device_ledger" && payload.device_id) {
        navigate(`/ledger?device_id=${payload.device_id}`)
        return
      }

      const scannedPayload: ScannedPayload = payload
      if (!scannedPayload.o || !scannedPayload.a || !scannedPayload.d || !scannedPayload.s || !scannedPayload.p) {
        throw new Error("Invalid payload structure")
      }
      setScanResult(scannedPayload)
      verifyScannedPayload(scannedPayload)
    } catch (err) {
      setVerificationResult("failed")
    }
  }

  async function verifyScannedPayload(payload: ScannedPayload) {
    try {
      const canonicalPayload = createCanonicalPayload({
        operator_id: payload.o,
        action_type: payload.a,
        data_payload: payload.d,
      })

      console.log("SCANNER_VERIFYING_STRING", canonicalPayload)
      const isValid = await verifySignature(canonicalPayload, payload.s, payload.p)
      setVerificationResult(isValid ? "verified" : "failed")
    } catch (error) {
      setVerificationResult("failed")
    }
  }

  const resetScanner = () => {
    setScanResult(null)
    setVerificationResult(null)
    setScannerActive(true)
  }

  return (
    <div className="max-w-2xl mx-auto space-y-6">
      <div className="flex items-center space-x-3 mb-8 border-b pb-4">
        <div className="bg-muted p-2 rounded-full border">
          <WifiOff className="w-6 h-6 text-muted-foreground" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Air-Gapped Offline Scanner</h1>
          <p className="text-muted-foreground text-sm">
            Mathematically verify signed records without backend API access.
          </p>
        </div>
      </div>

      {!scanResult && scannerActive && (
        <Card className="border-2 border-dashed">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ScanLine className="w-5 h-5" />
              Scan Ledger QR
            </CardTitle>
            <CardDescription>
              Hold the generated high-density QR code up to your camera.
            </CardDescription>
          </CardHeader>
          <CardContent className="relative flex flex-col items-center justify-center min-h-[300px]">
            {cameraError && (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center p-6 text-center bg-destructive/10 backdrop-blur-sm rounded-lg border border-destructive">
                <ShieldAlert className="w-10 h-10 text-destructive mb-2" />
                <p className="font-semibold text-destructive">{cameraError}</p>
                <Button variant="outline" className="mt-4" onClick={() => setScannerActive(false)}>
                  Cancel Scan
                </Button>
              </div>
            )}
            {isStartingCamera && !cameraError && (
              <div className="absolute inset-0 z-10 flex flex-col items-center justify-center p-12 text-muted-foreground bg-background/80 backdrop-blur-sm rounded-lg">
                <Loader2 className="w-8 h-8 animate-spin mb-4" />
                <p>Requesting camera access...</p>
              </div>
            )}
            {/* The qr-reader div must NEVER have display: none (hidden) or dimensions collapse to 0 */}
            <div 
              id="qr-reader" 
              className="overflow-hidden rounded-lg bg-black/5" 
              style={{ minHeight: '300px', width: '100%' }}
            />
          </CardContent>
        </Card>
      )}

      {scanResult && verificationResult && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <Alert variant={verificationResult === "verified" ? "default" : "destructive"} 
                 className={verificationResult === "verified" ? "border-emerald-500 bg-emerald-500/10 text-emerald-700 dark:text-emerald-400" : ""}>
            {verificationResult === "verified" ? (
              <ShieldCheck className="h-5 w-5 !text-emerald-600 dark:!text-emerald-400" />
            ) : (
              <ShieldAlert className="h-5 w-5" />
            )}
            <AlertTitle className="text-lg font-bold">
              {verificationResult === "verified" ? "Mathematical Proof Verified" : "Signature Compromised"}
            </AlertTitle>
            <AlertDescription>
              {verificationResult === "verified" 
                ? "The Ed25519 cryptographic signature perfectly matches the payload and public key. This record is authentic and untampered."
                : "The cryptographic signature failed mathematical verification. This record has been tampered with or forged!"}
            </AlertDescription>
          </Alert>

          <Card>
            <CardHeader>
              <CardTitle>Decoded Payload</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 border-b pb-2">
                <span className="font-semibold text-muted-foreground">Operator ID</span>
                <span className="col-span-2 font-medium">{scanResult.o}</span>
              </div>
              <div className="grid grid-cols-3 border-b pb-2">
                <span className="font-semibold text-muted-foreground">Action Type</span>
                <span className="col-span-2 font-medium">{scanResult.a}</span>
              </div>
              <div className="grid grid-cols-3 border-b pb-2">
                <span className="font-semibold text-muted-foreground">Data Payload</span>
                <span className="col-span-2 font-mono text-sm break-all">{scanResult.d}</span>
              </div>
              <div className="grid grid-cols-3 border-b pb-2">
                <span className="font-semibold text-muted-foreground">Public Key</span>
                <span className="col-span-2 font-mono text-xs break-all text-muted-foreground">{scanResult.p}</span>
              </div>
              <div className="grid grid-cols-3">
                <span className="font-semibold text-muted-foreground">Signature</span>
                <span className="col-span-2 font-mono text-xs break-all text-muted-foreground">{scanResult.s}</span>
              </div>
            </CardContent>
          </Card>

          <Button onClick={resetScanner} className="w-full" size="lg">
            <ScanLine className="w-4 h-4 mr-2" />
            Scan Another Record
          </Button>
        </div>
      )}
    </div>
  )
}
