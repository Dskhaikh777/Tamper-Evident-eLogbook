import * as ed from '@noble/ed25519'
import { sha512 } from '@noble/hashes/sha2.js'

ed.hashes.sha512 = sha512


// Used to convert hex strings to Uint8Array and vice versa
export function bytesToHex(bytes: Uint8Array): string {
  return Array.from(bytes)
    .map((b) => b.toString(16).padStart(2, '0'))
    .join('')
}

export function hexToBytes(hex: string): Uint8Array {
  if (hex.length % 2 !== 0) throw new Error('Hex string must have an even number of characters')
  const bytes = new Uint8Array(hex.length / 2)
  for (let i = 0; i < hex.length; i += 2) {
    bytes[i / 2] = parseInt(hex.substring(i, i + 2), 16)
  }
  return bytes
}

// Constant separator identical to backend's app.core.hashing / app.utils.crypto_keys
export const FIELD_SEPARATOR = '\x1f'

export interface LogPayloadFields {
  operator_id: string
  action_type: string
  data_payload: string
}

/**
 * Generate a fresh Ed25519 keypair.
 * Returns both private and public keys as hex strings.
 */
export function generateKeyPair(): { privateKeyHex: string; publicKeyHex: string } {
  const privateKey = new Uint8Array(32)
  crypto.getRandomValues(privateKey)
  const publicKey = ed.getPublicKey(privateKey)

  return {
    privateKeyHex: bytesToHex(privateKey),
    publicKeyHex: bytesToHex(publicKey),
  }
}

/**
 * Construct the canonical string matching the backend's format exactly.
 * (operator_id || \x1f || action_type || \x1f || data_payload)
 */
export function createCanonicalPayload(data: LogPayloadFields): string {
  return [data.operator_id, data.action_type, data.data_payload].join(FIELD_SEPARATOR)
}

/**
 * Sign a payload with a given Ed25519 private key.
 * 
 * @param canonicalPayload The canonical formatted string.
 * @param privateKeyHex The hex-encoded Ed25519 private key (32 bytes -> 64 chars).
 * @returns Promise resolving to the hex-encoded signature (64 bytes -> 128 chars).
 */
export async function signPayload(canonicalPayload: string, privateKeyHex: string): Promise<string> {
  const messageBytes = new TextEncoder().encode(canonicalPayload)
  const privateKeyBytes = hexToBytes(privateKeyHex)
  
  const signatureBytes = await ed.signAsync(messageBytes, privateKeyBytes)
  return bytesToHex(signatureBytes)
}

/**
 * Verify an Ed25519 signature.
 * 
 * @param canonicalPayload The canonical formatted string.
 * @param signatureHex The hex-encoded signature.
 * @param publicKeyHex The hex-encoded public key.
 * @returns Promise resolving to a boolean indicating verification success.
 */
export async function verifySignature(
  canonicalPayload: string,
  signatureHex: string,
  publicKeyHex: string
): Promise<boolean> {
  try {
    const messageBytes = new TextEncoder().encode(canonicalPayload)
    const signatureBytes = hexToBytes(signatureHex)
    const publicKeyBytes = hexToBytes(publicKeyHex)

    return await ed.verifyAsync(signatureBytes, messageBytes, publicKeyBytes)
  } catch (error) {
    return false
  }
}
