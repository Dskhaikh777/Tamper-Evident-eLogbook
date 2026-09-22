import { createApi } from "@reduxjs/toolkit/query/react"
import { axiosBaseQuery } from "./baseQuery"

export interface LogEntryRequest {
  operator_id: string
  action_type: string
  data_payload: string
  signature: string
  public_key: string
  raw_payload: string
}

export interface LogEntryResponse {
  id: string
  device_id: string
  operator_id: number
  operator_employee_id: string
  action_type: string
  data_payload: string
  timestamp: string
  signature: string
  public_key: string
  previous_hash: string
  current_hash: string
  is_chain_intact: boolean
}

export interface BreachedDecoyDetail {
  id: number
  decoy_name: string
  accessed_count: number
  last_breach_timestamp: string | null
}

export type ThreatStatus = 
  | { status: "secure"; integrity: string; message: string }
  | {
      status: "critical"
      integrity: string
      message: string
      total_decoys: number
      breached_count: number
      breached_nodes: BreachedDecoyDetail[]
    }

export type LedgerVerificationResult = 
  | { status: "valid"; message: string; blocks_verified: number }
  | { 
      status: "tampered"
      message: string
      tampered_block_id: number
      expected_hash: string
      stored_hash: string 
    }

export interface DeviceOverview {
  id: string
  name: string
  model_number: string
  location: string
  last_action_state: {
    action: string
    performed_by: string
    time: string
  } | null
}

export const ledgerApi = createApi({
  reducerPath: "ledgerApi",
  baseQuery: axiosBaseQuery(),
  tagTypes: ["LogEntry", "ThreatStatus", "Devices"],
  endpoints: (builder) => ({
    createLog: builder.mutation<LogEntryResponse, LogEntryRequest & { device_id: string }>({
      query: (data) => ({
        url: `/ledger/${data.device_id}`,
        method: "POST",
        data,
      }),
      invalidatesTags: ["LogEntry", "Devices"],
    }),
    fetchLogs: builder.query<LogEntryResponse[], { device_id?: string } | void>({
      query: (params) => ({
        url: "/logs/",
        method: "GET",
        params: params || undefined,
      }),
      providesTags: ["LogEntry"],
    }),
    verifyLedger: builder.query<LedgerVerificationResult, void>({
      query: () => ({
        url: "/verify-ledger/",
        method: "GET",
      }),
      // Intentionally not providing tags so it doesn't auto-cache or poll
      // We want to manually trigger this and get fresh results
    }),
    triggerHoneypotTrap: builder.mutation<void, void>({
      query: () => ({
        url: "/system-configs-internal/",
        method: "GET",
      }),
      // Intentionally invalidates ThreatStatus to force an immediate refresh 
      // of the SOC Dashboard on the next poll cycle or instantly
      invalidatesTags: ["ThreatStatus"],
    }),
    fetchThreatStatus: builder.query<ThreatStatus, void>({
      query: () => ({
        url: "/threat-status/",
        method: "GET",
      }),
      providesTags: ["ThreatStatus"],
    }),
    getDevicesOverview: builder.query<DeviceOverview[], void>({
      query: () => ({
        url: "/devices/overview",
        method: "GET",
      }),
      providesTags: ["Devices"],
    }),
    createUser: builder.mutation<any, any>({
      query: (data) => ({
        url: "/admin/users",
        method: "POST",
        data,
      }),
    }),
    createDevice: builder.mutation<any, any>({
      query: (data) => ({
        url: "/admin/devices",
        method: "POST",
        data,
      }),
      invalidatesTags: ["Devices"],
    }),
  }),
})

export const { 
  useCreateLogMutation, 
  useFetchLogsQuery, 
  useLazyVerifyLedgerQuery,
  useTriggerHoneypotTrapMutation,
  useFetchThreatStatusQuery,
  useGetDevicesOverviewQuery,
  useCreateUserMutation,
  useCreateDeviceMutation
} = ledgerApi
