import { createSlice } from '@reduxjs/toolkit'
import type { PayloadAction } from '@reduxjs/toolkit'
import { generateKeyPair } from '@/lib/crypto'

export type Role = 'operator' | 'admin' | 'auditor' | 'OPERATOR' | 'ADMIN' | 'AUDITOR'

interface User {
  id: string
  name: string
  role: Role
}

interface KeyPair {
  publicKey: string
  privateKey: string
}

interface AuthState {
  user: User | null
  keyPair: KeyPair | null
  accessToken: string | null
  isAuthenticated: boolean
}

// Helper to load from LocalStorage
const loadState = (): AuthState => {
  try {
    const stored = localStorage.getItem('elogbook_auth')
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (err) {
    console.error('Failed to parse auth state from local storage', err)
  }
  return {
    user: null,
    keyPair: null,
    accessToken: null,
    isAuthenticated: false,
  }
}

// Initial state loaded from local storage
const initialState: AuthState = loadState()

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    loginSuccess(state, action: PayloadAction<{ user: User; accessToken: string }>) {
      state.user = action.payload.user
      state.accessToken = action.payload.accessToken
      state.isAuthenticated = true
      localStorage.setItem('elogbook_auth', JSON.stringify(state))
    },
    setKeys(state, action: PayloadAction<KeyPair>) {
      state.keyPair = action.payload
      localStorage.setItem('elogbook_auth', JSON.stringify(state))
    },
    generateNewIdentity(state) {
      const keys = generateKeyPair()
      
      state.keyPair = {
        publicKey: keys.publicKeyHex,
        privateKey: keys.privateKeyHex,
      }
      
      localStorage.setItem('elogbook_auth', JSON.stringify(state))
    },
    logout(state) {
      state.user = null
      state.keyPair = null
      state.accessToken = null
      state.isAuthenticated = false
      localStorage.removeItem('elogbook_auth')
    }
  },
})

export const { loginSuccess, setKeys, generateNewIdentity, logout } = authSlice.actions
export default authSlice.reducer
