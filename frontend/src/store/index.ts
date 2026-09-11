import { configureStore } from "@reduxjs/toolkit"
import authReducer from "./slices/authSlice"
import { ledgerApi } from "@/services/api/ledgerApi"

export const store = configureStore({
  reducer: {
    auth: authReducer,
    [ledgerApi.reducerPath]: ledgerApi.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: false,
    }).concat(ledgerApi.middleware),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
