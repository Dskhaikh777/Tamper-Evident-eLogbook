import { useState } from "react"
import { useDispatch, useSelector } from "react-redux"
import type { RootState } from "@/store"
import { generateNewIdentity } from "@/store/slices/authSlice"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Input } from "@/components/ui/input"
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"
import { Copy, Eye, EyeOff, KeyRound, ShieldAlert, QrCode } from "lucide-react"
import { QRCodeSVG } from "qrcode.react"

export function KeysPage() {
  const dispatch = useDispatch()
  const { user, keyPair, isAuthenticated } = useSelector((state: RootState) => state.auth)
  
  const [showPrivateKey, setShowPrivateKey] = useState(false)
  const [copiedPublic, setCopiedPublic] = useState(false)

  const handleGenerateKeys = () => {
    dispatch(generateNewIdentity())
  }

  const copyToClipboard = async (text: string) => {
    if (!text) return
    await navigator.clipboard.writeText(text)
    setCopiedPublic(true)
    setTimeout(() => setCopiedPublic(false), 2000)
  }

  if (!isAuthenticated || !user || !keyPair) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-center">
        <KeyRound className="w-12 h-12 text-muted-foreground mb-4" />
        <h2 className="text-2xl font-bold mb-2">No Active Identity</h2>
        <p className="text-muted-foreground mb-6">
          Generate an Ed25519 cryptographic identity to sign log entries.
        </p>
        <Button onClick={handleGenerateKeys}>Generate New Keypair</Button>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight mb-2">System Keys</h1>
        <p className="text-muted-foreground">
          Manage your Ed25519 cryptographic identity for FDA 21 CFR Part 11 compliant non-repudiation.
        </p>
      </div>

      <div className="grid gap-6 md:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-emerald-500" />
              Active Identity
            </CardTitle>
            <CardDescription>Current mock session details.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-1">Operator ID</p>
                <p className="font-semibold">{user.id}</p>
              </div>
              <div>
                <p className="text-sm font-medium text-muted-foreground mb-1">Role</p>
                <Badge variant={user.role === 'OPERATOR' ? 'default' : 'secondary'}>
                  {user.role}
                </Badge>
              </div>
            </div>
          </CardContent>
          <CardFooter>
            <Button variant="outline" onClick={handleGenerateKeys} className="w-full">
              Regenerate Identity
            </Button>
          </CardFooter>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Public Key</CardTitle>
            <CardDescription>Your public identifier, used by auditors for verification.</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex space-x-2">
              <Input
                readOnly
                value={keyPair.publicKey}
                className="font-mono text-xs bg-muted"
              />
              <Button
                variant="secondary"
                size="icon"
                onClick={() => copyToClipboard(keyPair.publicKey)}
                title="Copy Public Key"
              >
                <Copy className="w-4 h-4" />
              </Button>
              <Dialog>
                <DialogTrigger asChild>
                  <Button variant="secondary" size="icon" title="View QR">
                    <QrCode className="w-4 h-4" />
                  </Button>
                </DialogTrigger>
                <DialogContent className="sm:max-w-md flex flex-col items-center justify-center p-6">
                  <DialogHeader>
                    <DialogTitle className="text-center mb-4">Public Key QR</DialogTitle>
                  </DialogHeader>
                  <div className="bg-white p-4 rounded-md">
                    <QRCodeSVG value={keyPair.publicKey} size={200} />
                  </div>
                  <p className="text-sm text-muted-foreground mt-4 text-center break-all font-mono">
                    {keyPair.publicKey}
                  </p>
                </DialogContent>
              </Dialog>
            </div>
            {copiedPublic && <p className="text-xs text-emerald-500">Copied to clipboard!</p>}
          </CardContent>
        </Card>

        <Card className="md:col-span-2 border-amber-500/50">
          <CardHeader>
            <CardTitle className="text-amber-500 flex items-center gap-2">
              <ShieldAlert className="w-5 h-5" />
              Private Key (Confidential)
            </CardTitle>
            <CardDescription>
              Never share this key. It is used to generate legally binding digital signatures.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="flex space-x-2">
              <Input
                type={showPrivateKey ? "text" : "password"}
                readOnly
                value={showPrivateKey ? keyPair.privateKey : "••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••••"}
                className="font-mono text-xs bg-muted text-amber-600 dark:text-amber-400"
              />
              <Button
                variant="outline"
                size="icon"
                onClick={() => setShowPrivateKey(!showPrivateKey)}
                className="shrink-0 border-amber-500/30 hover:bg-amber-500/10"
              >
                {showPrivateKey ? <EyeOff className="w-4 h-4 text-amber-500" /> : <Eye className="w-4 h-4 text-amber-500" />}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
