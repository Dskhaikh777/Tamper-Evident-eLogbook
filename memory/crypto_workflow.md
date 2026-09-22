# Cryptography Workflow

This document details the exact schemas and steps to guarantee zero-trust data immutability and offline air-gapped verification across the stack.

## 1. Data Structures & Schemas

### Client-Side Logging Schema
When an operator submits a log entry, the client constructs the following shape:
```typescript
interface LogEntryPayload {
  operator_id: string;
  action_type: string;
  data_payload: string;
}

interface SignedLogEntry extends LogEntryPayload {
  public_key: string; // 64-character hex Ed25519 public key
  signature: string;  // 128-character hex Ed25519 signature
}
```

### Canonical Signing String
**CRITICAL:** The client must construct the exact string the FastAPI backend expects to verify the signature. 
*   **Delimiter:** ASCII Unit Separator `\x1f`
*   **Format:** `operator_id + '\x1f' + action_type + '\x1f' + data_payload`

## 2. Operator Workflow (Data Entry & Signing)

1.  **Authentication:** Operator logs in. App securely holds their Ed25519 Private Key in memory.
2.  **Form Completion:** Operator fills out the New Log Entry form (`action_type`, `data_payload`).
3.  **Canonical String Generation:** App builds the delimited string on submission.
4.  **Signing:** App uses `@noble/ed25519` to sign the canonical UTF-8 encoded string using the Private Key.
5.  **Submission:** The `SignedLogEntry` JSON is sent to FastAPI `POST /logs/`.
6.  **QR Code Generation:** Upon 201 Created from backend, the app generates a high-density QR code embedding a JSON string containing the `operator_id`, `action_type`, `data_payload`, `public_key`, and `signature`.

## 3. Auditor Workflow (Air-Gapped Offline Verification)

1.  **Scanner Access:** Auditor navigates to the Offline Scanner interface on an air-gapped mobile device/tablet.
2.  **Code Scan:** `html5-qrcode` utilizes the device camera to scan the operator's generated QR code from a screen or printout.
3.  **Payload Extraction:** App parses the JSON payload contained within the QR code.
4.  **Verification Engine:** 
    *   App reconstructs the canonical string from the extracted fields.
    *   App uses `@noble/ed25519` to mathematically verify the `signature` against the canonical string and `public_key`.
5.  **UI Feedback:** App displays a highly visible "VERIFIED - SECURE" (Emerald Green) or "TAMPERED - INVALID" (Crimson Red) state.
