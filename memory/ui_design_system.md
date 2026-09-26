# UI Design System: "Clinical High-Trust"

The interface must convey precision, security, and cleanliness—hallmarks of pharmaceutical and healthcare compliance. It supports dual-mode design (WCAG 2.1 AA/AAA compliant) for bright manufacturing floors and dark-room SOC environments.

## 1. Theming Strategy (Tailwind CSS)
We utilize a dynamic Light/Dark mode controlled by a `ThemeProvider` adding/removing the `.dark` class to the HTML root.

### Clinical High-Trust Light
- **Backgrounds:** Crisp clean slates (`bg-slate-50`), clinical blue surfaces (`bg-white`).
- **Borders:** High-contrast for clear delineation (`border-slate-200`).
- **Elevations:** Subtle shadows for depth.

### SOC Dark
- **Backgrounds:** Deep slate/zinc (`bg-zinc-950` or `bg-slate-900`), slightly lighter surface cards (`bg-zinc-900`).
- **Borders:** Subtle muted outlines (`border-zinc-800`).
- **Glowing Status Accents:** Used sparingly on dark mode to highlight cryptographic state.

## 2. Status Colors (Cross-Theme)
- **Verified / Safe:** Emerald Green (`text-emerald-500`, `bg-emerald-500/10`) — Indicates intact hash chains and secure honey-tokens.
- **Tampered / Breached:** Crimson Red (`text-red-500`, `bg-red-500/10`) — Indicates tripped honeypots or broken cryptographic chains.
- **Pending / Caution:** Amber (`text-amber-500`, `bg-amber-500/10`).

## 3. Typography: National Park
The "National Park" sans-serif font family drives the entire UI, chosen for its clear, highly legible geometric properties suitable for data-dense displays.

- **Headings (h1-h4):** `font-semibold` or `font-bold` with tight tracking (`tracking-tight`).
- **Body:** `font-normal` with relaxed leading for readability (`leading-relaxed`).
- **Tabular Data:** Tabular numbers (`tabular-nums`) and monospace variants where applicable for cryptographic hashes. Keys and hashes should truncate with `...` but support one-click copy.

## 4. Modern Design Principles
- **Data Density:** High density layouts using tables and grids to show complex ledger records without excessive scrolling.
- **Explicit Feedback:** 
  - Skeleton loaders for asynchronous data fetching (RTK Query loading states).
  - Toast alerts (via shadcn/ui) for successful signings, verifications, and errors.
- **Micro-Interactions:** Subtle state transitions (hover, active, focus-visible) and visual feedback during computationally heavy operations like chain verification.
