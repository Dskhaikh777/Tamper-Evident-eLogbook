# Tamper-Evident eLogbook

A high-trust, cryptographically secured electronic logbook designed to maintain immutable audit trails in compliance with **FDA 21 CFR Part 11** and **ALCOA+** principles. This application utilizes client-side Ed25519 digital signatures, server-side SHA3-256 blockchain hashing, and a real-time honeypot threat dashboard.

## 🌟 Core Features

- **Zero-Trust Cryptography**: Ed25519 Public/Private keypairs are generated entirely in the browser. Private keys never touch the network.
- **Immutable Blockchain Ledger**: Every log entry is deterministically signed and chronologically linked using SHA3-256 hashes.
- **Air-Gapped Auditing**: Embeds raw payload data and cryptographic signatures into high-density QR codes for offline, mathematics-based verification on isolated devices.
- **Proactive Threat Detection (SOC)**: A real-time threat dashboard polling a network of decoy "honeypot" database nodes to instantly detect network reconnaissance and lateral movement.
- **Strict Role-Based Access Control (RBAC)**: JWT-secured endpoints explicitly segregating Operator (Data Entry), Auditor (Read-Only/Scan), and Admin (Full Access/SOC) capabilities.

## 🛠️ Technology Stack

**Frontend:**
- React 19 + TypeScript
- Vite
- Tailwind CSS v4 + shadcn/ui
- Redux Toolkit (RTK Query for API state)
- `@noble/ed25519` (Client-side Cryptography)

**Backend:**
- Python 3.10+
- FastAPI
- PostgreSQL + SQLAlchemy
- Passlib & python-jose (JWT Auth & bcrypt hashing)

---

## 🚀 Getting Started

### Prerequisites
- Node.js 20+
- Python 3.10+
- PostgreSQL database running locally or via Docker

### 1. Backend Setup (FastAPI)

Navigate to the project root and create a virtual environment:
```bash
python -m venv .venv
source .venv/Scripts/activate  # Windows
# source .venv/bin/activate    # Mac/Linux
```

Install dependencies:
```bash
pip install -r requirements.txt
```

Configure Environment Variables:
Copy `.env.example` to `.env` and configure your PostgreSQL database URL and JWT Secret.
```bash
cp .env.example .env
```

Start the FastAPI Server:
```bash
uvicorn app.main:app --reload
```
The backend API and Swagger UI will be available at: [http://localhost:8000/docs](http://localhost:8000/docs)

### 2. Frontend Setup (React/Vite)

Open a new terminal, navigate to the `frontend` directory:
```bash
cd frontend
```

Install NPM packages:
```bash
npm install
```

Start the Vite Development Server:
```bash
npm run dev
```
The frontend will be available at: [http://localhost:5173](http://localhost:5173)

---

## 🧪 Testing the Application

1. **Seed the Database**: Navigate to the React frontend at `http://localhost:5173`. You will be redirected to the Login page. Click the **"Seed Database Defaults"** button at the bottom to provision the initial accounts.
2. **Operator Flow**: Log in with username `operator` (password: `operator@secure123`). Navigate to the Keys page to generate an Ed25519 identity, then submit a new log entry.
3. **Admin Flow**: Sign out and log back in as `admin` (password: `admin@secure123`). Navigate to the Audit Ledger to view the immutable chain. Click **"Run Global Integrity Check"** to recalculate the SHA3-256 hashes.
4. **Threat Detection**: As an admin, navigate to the SOC Threat Dashboard and click **"Simulate Hostile Intrusion"** to trigger a fake honeypot breach.

