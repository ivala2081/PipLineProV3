import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface ExchangeRate {
  currency_pair: string;
  rate: number;
  source: string;
  data_quality: string;
  updated_at: string;
}

interface ExchangeRatesState {
  rates: Record<string, ExchangeRate>;
  loading: boolean;
  error: string | null;
  lastUpdated: Date | null;
  selectedDate: string;
}

const initialState: ExchangeRatesState = {
  rates: {},
  loading: false,
  error: null,
  lastUpdated: null,
  selectedDate: new Date().toISOString().slice(0, 10),
};

const exchangeRatesSlice = createSlice({
  name: 'exchangeRates',
  initialState,
  reducers: {
    setRates: (state, action: PayloadAction<Record<string, ExchangeRate>>) => {
      state.rates = action.payload;
      state.lastUpdated = new Date();
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setSelectedDate: (state, action: PayloadAction<string>) => {
      state.selectedDate = action.payload;
    },
    updateRate: (state, action: PayloadAction<{ currencyPair: string; rate: ExchangeRate }>) => {
      state.rates[action.payload.currencyPair] = action.payload.rate;
      state.lastUpdated = new Date();
    },
    clearRates: (state) => {
      state.rates = {};
      state.lastUpdated = null;
    },
    clearError: (state) => {
      state.error = null;
    },
  },
});

export const {
  setRates,
  setLoading,
  setError,
  setSelectedDate,
  updateRate,
  clearRates,
  clearError,
} = exchangeRatesSlice.actions;

export default exchangeRatesSlice.reducer;
