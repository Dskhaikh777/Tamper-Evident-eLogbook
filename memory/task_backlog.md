# Task Backlog

Development occurs in logical, sequential sprints.

## Sprint 1: Project Setup & Memory Initialization
- [x] Create `/memory` directory and write architecture, crypto workflow, UI design, and task backlog documentation.
- [x] Update Memory Protocol to Architecture Revision 2 (Tailwind, shadcn, RTK, National Park font).

## Sprint 2: Framework Initialization & Base App Shell
- [x] Initialize Vite + React (TypeScript) repository.
- [x] Configure Tailwind CSS, shadcn/ui CLI configuration, and integrate the National Park font.
- [x] Implement `ThemeProvider` (Light/Dark/System toggle).
- [x] Set up Redux Toolkit store with RTK Query and Axios integration.
- [x] Build the base Clinical High-Trust App Shell (collapsible sidebar, security status header, theme toggle, and React Router outlet).

## Sprint 3: Cryptography Module & Auth Mocking
- [x] Install cryptographic dependencies (`@noble/ed25519`).
- [x] Write `lib/crypto.ts` utility wrappers: Keypair generation, canonical payload builder, sign, and verify functions.
- [x] Set up Redux slice for Auth state.
- [x] Build Login Page (mocking JWT RBAC roles: `Operator` and `Admin`).

## Sprint 4: Operator Data Entry & API Integration
- [x] Build `NewLogEntryPage`: Form to capture operator logs.
- [x] Integrate React Hook Form + Zod for strict client-side validation.
- [x] Intercept form submission to invoke the `crypto.ts` signing module automatically using the logged-in Operator's private key.
- [x] Configure RTK Query endpoint for `POST /logs/` and dispatch the structured, signed payload.

## Sprint 5: Ledger View & Threat Dashboard (Admin)
- [x] Build `LedgerViewPage`: Fetch `/logs/` via RTK Query and display immutable audit trail.
- [x] Add manual "Verify Ledger" trigger calling `GET /verify-ledger/` and visualizing the intact chain.
- [x] Build `ThreatDashboardPage`: Set up polling for `GET /threat-status/`. Build critical alert UI for honey-token breaches.

## Sprint 6: Air-Gapped QR Code Generation & Offline Scanning
- [x] Install `qrcode` and `html5-qrcode`.
- [x] Build `QRCodeGenerator`: Embed signed payloads into high-density QR codes on `LedgerTable`.
- [x] Build `OfflineScannerPage`: Scan QR -> reconstruct payload -> verify mathematical signature locally (zero backend API calls).

## Sprint 7: Final Polish & Audit
- [x] Refine micro-animations and accessibility features.
- [x] Ensure 100% typing strictness and zero warnings.
- [x] Execute end-to-end simulated workflow without backend.
- [x] Finalize frontend and mark as ready for backend integration.
