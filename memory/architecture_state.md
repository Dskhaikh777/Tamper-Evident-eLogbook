# Architecture State

## Tech Stack Selection
**Framework:** React 18+ (initialized via Vite for optimal build speeds and developer experience) + TypeScript for strict typing.
**Styling & UI Components:** Tailwind CSS combined with `shadcn/ui` (built on Radix UI primitives) and `lucide-react` for iconography.
**Theming:** Dynamic Dark/Light mode switching using Tailwind's `class` strategy (system preference detection and manual toggle).
**State Management & Caching:** Redux Toolkit (RTK) for global state, combined with RTK Query for data fetching. Standardized HTTP requests use an Axios-based `baseQuery` for centralized interceptors, caching, and token handling.
**Typography:** "National Park" sans-serif applied globally across display, body, and tabular data.
**Routing:** React Router v6.
**Cryptography:** `@noble/ed25519` (Audited, pure JS/TS implementation of Ed25519 for browser use without native bindings).
**QR Code Generation:** `qrcode` (Reliable canvas/SVG based QR generation).
**QR Code Scanning:** `html5-qrcode` (Robust client-side camera access and decoding for offline air-gapped environments).

## Directory Structure
```text
/src
  /assets              # Static assets (fonts, icons, logos)
  /components          # Reusable UI components
    /ui                # shadcn/ui primitives
    /layout            # AppShell, Sidebar, Header, ThemeProvider
  /features            # Domain-specific feature modules
    /auth              # Login forms, RBAC slice
    /ledger            # Log list, immutable chain visualization
    /scanner           # QR code generation and offline scanning interface
    /threat-monitor    # Real-time SOC dashboard
  /hooks               # Custom React hooks
  /lib                 # Utility libraries
    utils.ts           # Tailwind merge/clsx utilities
    crypto.ts          # @noble/ed25519 wrapper functions
  /pages               # Routable page components mapped to React Router
  /services            # API services
    /api               # Axios client and RTK baseQuery
  /store               # Redux Toolkit setup
    index.ts           # configureStore
    rootReducer.ts     # Combined reducers/slices
  /styles              # Global CSS (Tailwind directives)
  App.tsx              # Root component & Router definition
  main.tsx             # React DOM entry point
```

## Component Hierarchy
- `App` (Provider wrappers: Redux, ThemeProvider, Router)
  - `AuthLayout`
    - `LoginPage` (Operator & Admin login)
  - `AppShell` (RBAC Protected Route Wrapper)
    - `Header` (Theme Toggle, Auth Badge, Status)
    - `Sidebar` (Navigation)
    - **Operator Routes:**
      - `NewLogEntryPage` (Data Entry Form -> Ed25519 Sign -> QR Generate)
    - **Admin/Auditor Routes:**
      - `LedgerViewPage` (Immutable audit trail display)
      - `ThreatDashboardPage` (SOC monitor polling `/threat-status/`)
      - `OfflineScannerPage` (Air-gapped QR verification using device camera)
