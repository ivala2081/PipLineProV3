import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export interface User {
  id: number;
  username: string;
  role: string;
  admin_level: number;
  admin_title: string;
  is_active: boolean;
  email?: string;
  created_at?: string;
  last_login?: string;
  failed_login_attempts: number;
  account_locked_until?: string;
  created_by?: number;
  permissions: Record<string, boolean>;
}

interface UserState {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

const initialState: UserState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
};

const userSlice = createSlice({
  name: 'user',
  initialState,
  reducers: {
    setUser: (state, action: PayloadAction<User | null>) => {
      state.user = action.payload;
      state.isAuthenticated = !!action.payload;
    },
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.isLoading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    clearUser: (state) => {
      state.user = null;
      state.isAuthenticated = false;
      state.error = null;
    },
    updateUserPermissions: (state, action: PayloadAction<Record<string, boolean>>) => {
      if (state.user) {
        state.user.permissions = action.payload;
      }
    },
  },
});

export const {
  setUser,
  setLoading,
  setError,
  clearUser,
  updateUserPermissions,
} = userSlice.actions;

export default userSlice.reducer;
