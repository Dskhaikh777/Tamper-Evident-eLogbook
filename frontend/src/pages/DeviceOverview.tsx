import { useNavigate } from "react-router-dom"
import { useSelector } from "react-redux"
import { useGetDevicesOverviewQuery } from "@/services/api/ledgerApi"
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Cpu, ServerCrash, Clock, FileSignature, MapPin, Plus } from "lucide-react"
import { DeviceQRCodeGenerator } from "@/components/qr/DeviceQRCodeGenerator"

export function DeviceOverview() {
  const { data: devices, isLoading, error } = useGetDevicesOverviewQuery(undefined, {
    pollingInterval: 15000,
  })
  const navigate = useNavigate()
  const role = useSelector((state: any) => state.auth?.user?.role)
  const isAdmin = role === "ADMIN" || role === "admin"

  if (isLoading) {
    return (
      <div className="max-w-6xl mx-auto space-y-6">
        <div className="flex items-center space-x-3 mb-8 border-b pb-4">
          <Skeleton className="w-10 h-10 rounded-full" />
          <div>
            <Skeleton className="h-8 w-64 mb-2" />
            <Skeleton className="h-4 w-96" />
          </div>
        </div>
        <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          {[1, 2, 3, 4, 5, 6].map(i => (
            <Skeleton key={i} className="h-64 rounded-xl" />
          ))}
        </div>
      </div>
    )
  }

  if (error || !devices) {
    return (
      <Card className="border-destructive max-w-3xl mx-auto mt-12">
        <CardContent className="flex flex-col justify-center items-center h-64 text-center">
          <ServerCrash className="h-12 w-12 text-destructive mb-4" />
          <h2 className="text-xl font-bold">Network Offline</h2>
          <p className="text-muted-foreground">Unable to reach the edge device grid.</p>
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="max-w-6xl mx-auto space-y-6">
      <div className="flex items-center justify-between mb-8 border-b pb-4">
        <div className="flex items-center space-x-3">
          <div className="bg-blue-500/10 p-2 rounded-full border border-blue-500/20">
            <Cpu className="w-6 h-6 text-blue-600" />
          </div>
          <div>
            <h1 className="text-3xl font-bold tracking-tight">Smart Grid Overview</h1>
            <p className="text-muted-foreground text-sm">
              Monitor registered edge devices and their cryptographic operation state.
            </p>
          </div>
        </div>
        
        {isAdmin && (
          <Button onClick={() => navigate('/admin')} className="gap-2">
            <Plus className="w-4 h-4" />
            Register Hardware
          </Button>
        )}
      </div>

      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {devices.map((device) => (
          <Card key={device.id} className="flex flex-col">
            <CardHeader>
              <div className="flex justify-between items-start">
                <CardTitle className="text-xl font-bold">{device.name}</CardTitle>
                <Badge variant="outline" className="font-mono text-xs">{device.model_number}</Badge>
              </div>
              <CardDescription className="flex items-center gap-1 mt-2">
                <MapPin className="h-3 w-3" /> {device.location}
              </CardDescription>
            </CardHeader>
            <CardContent className="flex-1">
              <div className="bg-muted/50 p-4 rounded-lg border">
                <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Clock className="h-4 w-4 text-muted-foreground" />
                  Last Operation
                </h4>
                {device.last_operation ? (
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Action:</span>
                      <span className="font-medium">{device.last_operation.action}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Operator:</span>
                      <span className="font-mono text-xs">{device.last_operation.operator}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Time:</span>
                      <span>{new Date(device.last_operation.timestamp).toLocaleTimeString()}</span>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-4 text-muted-foreground text-sm italic">
                    No Operations Yet
                  </div>
                )}
              </div>
            </CardContent>
            <CardFooter className="flex space-x-2">
              <Button 
                onClick={() => navigate(`/log-entry/${device.id}`)}
                className="flex-1 bg-blue-600 hover:bg-blue-700 text-white"
              >
                <FileSignature className="w-4 h-4 mr-2" />
                Log New Activity
              </Button>
              <DeviceQRCodeGenerator device={device} />
            </CardFooter>
          </Card>
        ))}
        {devices.length === 0 && (
          <div className="col-span-full text-center py-12 text-muted-foreground">
            No devices are registered to the grid. Use the Admin Control Panel to register hardware.
          </div>
        )}
      </div>
    </div>
  )
}
