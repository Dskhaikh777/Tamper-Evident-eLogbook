import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom"
import { ThemeProvider } from "@/components/theme/ThemeProvider"
import { AppShell } from "@/components/layout/AppShell"
import { ProtectedRoute } from "@/components/auth/ProtectedRoute"
import { KeysPage } from "@/pages/KeysPage"
import { NewLogEntryPage } from "@/pages/NewLogEntryPage"
import { Toaster } from "@/components/ui/sonner"
import { LoginPage } from "@/pages/LoginPage"

import { LedgerViewPage } from "@/pages/LedgerViewPage"
import { ThreatDashboardPage } from "@/pages/ThreatDashboardPage"
import { OfflineScannerPage } from "@/pages/OfflineScannerPage"
import { DeviceOverview } from "@/pages/DeviceOverview"
import { AdminDashboard } from "@/pages/AdminDashboard"

function App() {
  return (
    <ThemeProvider defaultTheme="system" storageKey="elogbook-ui-theme">
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          
          <Route path="/" element={<AppShell />}>
            <Route index element={<Navigate to="/keys" replace />} />
            
            {/* All authenticated users can access devices */}
            <Route element={<ProtectedRoute allowedRoles={['OPERATOR', 'ADMIN', 'AUDITOR', 'operator', 'admin', 'auditor']} />}>
              <Route path="devices" element={<DeviceOverview />} />
            </Route>

            {/* Operators can access keys (no admins or auditors) */}
            <Route element={<ProtectedRoute allowedRoles={['OPERATOR', 'operator']} />}>
              <Route path="keys" element={<KeysPage />} />
            </Route>

            {/* OPERATOR Only */}
            <Route element={<ProtectedRoute allowedRoles={['OPERATOR', 'operator']} />}>
              <Route path="log-entry/:deviceId" element={<NewLogEntryPage />} />
            </Route>

            {/* ADMIN / AUDITOR Only */}
            <Route element={<ProtectedRoute allowedRoles={['ADMIN', 'AUDITOR', 'admin', 'auditor']} />}>
              <Route path="ledger" element={<LedgerViewPage />} />
              <Route path="scan" element={<OfflineScannerPage />} />
            </Route>

            {/* ADMIN Only */}
            <Route element={<ProtectedRoute allowedRoles={['ADMIN', 'admin']} />}>
              <Route path="admin" element={<AdminDashboard />} />
              <Route path="threats" element={<ThreatDashboardPage />} />
            </Route>
          </Route>
        </Routes>
      </BrowserRouter>
      <Toaster />
    </ThemeProvider>
  )
}

export default App
