import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface UserSettings {
  language: string;
  theme: 'light' | 'dark' | 'auto';
  timezone: string;
  currency: string;
  dateFormat: string;
  notifications: {
    email: boolean;
    push: boolean;
    sms: boolean;
  };
  dashboard: {
    defaultTimeRange: string;
    autoRefresh: boolean;
    refreshInterval: number;
    showCharts: boolean;
    showMetrics: boolean;
  };
}

interface SettingsState {
  settings: UserSettings;
  isLoading: boolean;
  error: string | null;
}

const initialState: SettingsState = {
  settings: {
    language: 'en',
    theme: 'light',
    timezone: 'UTC',
    currency: '₺',
    dateFormat: 'YYYY-MM-DD',
    notifications: {
      email: true,
      push: false,
      sms: false,
    },
    dashboard: {
      defaultTimeRange: '7d',
      autoRefresh: true,
      refreshInterval: 300000, // 5 minutes
      showCharts: true,
      showMetrics: true,
    },
  },
  isLoading: false,
  error: null,
};

const settingsSlice = createSlice({
  name: 'settings',
  initialState,
  reducers: {
    setSettings: (state, action: PayloadAction<Partial<UserSettings>>) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    setLanguage: (state, action: PayloadAction<string>) => {
      state.settings.language = action.payload;
    },
    setTheme: (state, action: PayloadAction<'light' | 'dark' | 'auto'>) => {
      state.settings.theme = action.payload;
    },
    setCurrency: (state, action: PayloadAction<string>) => {
      state.settings.currency = action.payload;
    },
    setDashboardSettings: (state, action: PayloadAction<Partial<UserSettings['dashboard']>>) => {
      state.settings.dashboard = { ...state.settings.dashboard, ...action.payload };
    },
    setNotificationSettings: (state, action: PayloadAction<Partial<UserSettings['notifications']>>) => {
      state.settings.notifications = { ...state.settings.notifications, ...action.payload };
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    resetSettings: (state) => {
      state.settings = initialState.settings;
    },
  },
});

export const {
  setSettings,
  setLanguage,
  setTheme,
  setCurrency,
  setDashboardSettings,
  setNotificationSettings,
  setLoading,
  setError,
  resetSettings,
} = settingsSlice.actions;

export default settingsSlice.reducer;
