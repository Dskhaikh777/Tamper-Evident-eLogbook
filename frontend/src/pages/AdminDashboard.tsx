import { useState } from "react"
import { useForm } from "react-hook-form"
import { zodResolver } from "@hookform/resolvers/zod"
import * as z from "zod"
import { toast } from "sonner"
import { Server, UserPlus, Cpu, Loader2 } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Form,
  FormControl,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from "@/components/ui/form"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

import { 
  useCreateUserMutation, 
  useCreateDeviceMutation,
  useGetUsersQuery,
  useDeactivateUserMutation
} from "@/services/api/ledgerApi"

const operatorSchema = z.object({
  full_name: z.string().min(2, "Name must be at least 2 characters."),
  employee_id: z.string().min(4, "Employee ID is required."),
  password: z.string().min(8, "Password must be at least 8 characters."),
  role: z.enum(["operator", "admin", "auditor"]),
})

const deviceSchema = z.object({
  name: z.string().min(2, "Device name is required."),
  model_number: z.string().min(2, "Model number is required."),
  location: z.string().min(2, "Location is required."),
})

export function AdminDashboard() {
  const [activeTab, setActiveTab] = useState<"operators" | "devices">("operators")
  const { data: users, isLoading: isLoadingUsers, refetch: refetchUsers } = useGetUsersQuery()
  const [createUser, { isLoading: isCreatingUser }] = useCreateUserMutation()
  const [deactivateUser] = useDeactivateUserMutation()
  const [createDevice, { isLoading: isCreatingDevice }] = useCreateDeviceMutation()

  const operatorForm = useForm<z.infer<typeof operatorSchema>>({
    resolver: zodResolver(operatorSchema),
    defaultValues: {
      full_name: "",
      employee_id: "",
      password: "",
      role: "operator",
    },
  })

  const deviceForm = useForm<z.infer<typeof deviceSchema>>({
    resolver: zodResolver(deviceSchema),
    defaultValues: {
      name: "",
      model_number: "",
      location: "",
    },
  })

  async function onOperatorSubmit(values: z.infer<typeof operatorSchema>) {
    try {
      await createUser(values).unwrap()
      toast.success("User Provisioned", {
        description: `Successfully provisioned ${values.employee_id} as ${values.role}.`,
      })
      // Force manual refetch to guarantee the table updates
      await refetchUsers()
      // Explicitly reset form fields to empty strings
      operatorForm.reset({
        full_name: "",
        employee_id: "",
        password: "",
        role: "operator",
      })
    } catch (error: any) {
      toast.error("Provisioning Failed", {
        description: error?.data?.detail || "Could not provision user.",
      })
    }
  }

  async function handleDeactivateUser(userId: number, employeeId: string) {
    if (!confirm(`Are you sure you want to deactivate ${employeeId}?`)) return
    try {
      await deactivateUser(userId).unwrap()
      toast.success("User Deactivated", {
        description: `Successfully deactivated ${employeeId}.`,
      })
    } catch (error: any) {
      toast.error("Deactivation Failed", {
        description: error?.data?.detail || "Could not deactivate user.",
      })
    }
  }

  async function onDeviceSubmit(values: z.infer<typeof deviceSchema>) {
    try {
      await createDevice(values).unwrap()
      toast.success("Device Registered", {
        description: `Successfully registered device ${values.name} at ${values.location}.`,
      })
      deviceForm.reset()
    } catch (error: any) {
      toast.error("Registration Failed", {
        description: error?.data?.detail || "Could not register device.",
      })
    }
  }

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center space-x-3 mb-8 border-b pb-4">
        <div className="bg-primary/10 p-2 rounded-full border">
          <Server className="w-6 h-6 text-primary" />
        </div>
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Admin Control Panel</h1>
          <p className="text-muted-foreground text-sm">
            Provision new operators and register smart grid devices to the network.
          </p>
        </div>
      </div>

      <div className="w-full">
        <div className="grid w-full grid-cols-2 mb-8 bg-muted p-1 rounded-lg">
          <button
            type="button"
            className={`flex items-center justify-center gap-2 py-2 px-4 rounded-md text-sm font-medium transition-all ${
              activeTab === "operators" ? "bg-background shadow-sm" : "text-muted-foreground hover:bg-background/50"
            }`}
            onClick={() => setActiveTab("operators")}
          >
            <UserPlus className="w-4 h-4" /> Add User
          </button>
          <button
            type="button"
            className={`flex items-center justify-center gap-2 py-2 px-4 rounded-md text-sm font-medium transition-all ${
              activeTab === "devices" ? "bg-background shadow-sm" : "text-muted-foreground hover:bg-background/50"
            }`}
            onClick={() => setActiveTab("devices")}
          >
            <Cpu className="w-4 h-4" /> Register Device
          </button>
        </div>

        {activeTab === "operators" && (
          <div className="space-y-6">
            <Card>
              <CardHeader>
                <CardTitle>Manage Users</CardTitle>
                <CardDescription>
                  List of all registered system personnel (Admins, Auditors, and Operators).
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="rounded-md border">
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Employee ID</TableHead>
                        <TableHead>Full Name</TableHead>
                        <TableHead>Role</TableHead>
                        <TableHead>Status</TableHead>
                        <TableHead className="text-right">Actions</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {isLoadingUsers ? (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-6">
                            <Loader2 className="w-6 h-6 animate-spin mx-auto text-muted-foreground" />
                          </TableCell>
                        </TableRow>
                      ) : users && users.length > 0 ? (
                        users.map((user) => (
                          <TableRow key={user.id}>
                            <TableCell className="font-medium">{user.employee_id}</TableCell>
                            <TableCell>{user.full_name}</TableCell>
                            <TableCell>
                              <Badge variant="outline" className="capitalize">
                                {user.role}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {user.is_active ? (
                                <Badge className="bg-emerald-500/10 text-emerald-500 hover:bg-emerald-500/20 border-emerald-500/20">Active</Badge>
                              ) : (
                                <Badge variant="secondary">Deactivated</Badge>
                              )}
                            </TableCell>
                            <TableCell className="text-right">
                              <Button 
                                variant="destructive" 
                                size="sm" 
                                disabled={!user.is_active}
                                onClick={() => handleDeactivateUser(user.id, user.employee_id)}
                              >
                                Deactivate
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))
                      ) : (
                        <TableRow>
                          <TableCell colSpan={5} className="text-center py-6 text-muted-foreground">
                            No operators found.
                          </TableCell>
                        </TableRow>
                      )}
                    </TableBody>
                  </Table>
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Provision New User</CardTitle>
                <CardDescription>
                  Create a new user account with role-based access control.
                </CardDescription>
              </CardHeader>
            <CardContent>
              <Form {...operatorForm}>
                <form onSubmit={operatorForm.handleSubmit(onOperatorSubmit)} className="space-y-4">
                  <FormField
                    control={operatorForm.control}
                    name="full_name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Full Name</FormLabel>
                        <FormControl>
                          <Input placeholder="John Doe" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={operatorForm.control}
                    name="employee_id"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Employee ID</FormLabel>
                        <FormControl>
                          <Input placeholder="EMP-1045" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={operatorForm.control}
                    name="password"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Temporary Password</FormLabel>
                        <FormControl>
                          <Input type="password" placeholder="********" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={operatorForm.control}
                    name="role"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Access Level (Role)</FormLabel>
                        <Select onValueChange={field.onChange} defaultValue={field.value}>
                          <FormControl>
                            <SelectTrigger>
                              <SelectValue placeholder="Select a role" />
                            </SelectTrigger>
                          </FormControl>
                          <SelectContent>
                            <SelectItem value="operator">Operator (Data Entry)</SelectItem>
                            <SelectItem value="auditor">Auditor (View/Scan)</SelectItem>
                            <SelectItem value="admin">Administrator</SelectItem>
                          </SelectContent>
                        </Select>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <Button type="submit" disabled={isCreatingUser} className="w-full mt-6">
                    {isCreatingUser && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Provision Account
                  </Button>
                </form>
              </Form>
            </CardContent>
          </Card>
        </div>
      )}

        {activeTab === "devices" && (
          <Card>
            <CardHeader>
              <CardTitle>Register Edge Device</CardTitle>
              <CardDescription>
                Register a new smart grid edge device to append logs to its unique hardware chain.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Form {...deviceForm}>
                <form onSubmit={deviceForm.handleSubmit(onDeviceSubmit)} className="space-y-4">
                  <FormField
                    control={deviceForm.control}
                    name="name"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Device Name</FormLabel>
                        <FormControl>
                          <Input placeholder="Bio-Reactor Alpha" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={deviceForm.control}
                    name="model_number"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Model / Serial Number</FormLabel>
                        <FormControl>
                          <Input placeholder="SN-88294A" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <FormField
                    control={deviceForm.control}
                    name="location"
                    render={({ field }) => (
                      <FormItem>
                        <FormLabel>Physical Location</FormLabel>
                        <FormControl>
                          <Input placeholder="Lab 4, Sector B" {...field} />
                        </FormControl>
                        <FormMessage />
                      </FormItem>
                    )}
                  />
                  <Button type="submit" disabled={isCreatingDevice} className="w-full mt-6">
                    {isCreatingDevice && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                    Register Hardware
                  </Button>
                </form>
              </Form>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
