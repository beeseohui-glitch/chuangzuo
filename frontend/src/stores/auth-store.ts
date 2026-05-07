import { create } from 'zustand';
import { User, AuthState, LoginRequest } from '@/types';
import { auth } from '@/lib/auth';

interface AuthStore extends AuthState {
  login: (credentials: LoginRequest) => Promise<{ success: boolean; error?: string }>;
  logout: () => void;
  setUser: (user: User) => void;
  checkAuth: () => void;
}

export const useAuthStore = create<AuthStore>((set) => ({
  user: null,
  token: null,
  isAuthenticated: false,
  isLoading: true,

  login: async (credentials: LoginRequest) => {
    set({ isLoading: true });
    const result = await auth.login(credentials);

    if (result.success && result.data) {
      set({
        user: result.data.user,
        token: result.data.access_token,
        isAuthenticated: true,
        isLoading: false,
      });
      return { success: true };
    }

    set({ isLoading: false });
    return { success: false, error: result.error || 'Login failed' };
  },

  logout: () => {
    auth.logout();
    set({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  },

  setUser: (user: User) => {
    auth.setUser(user);
    set({ user });
  },

  checkAuth: () => {
    const token = auth.getToken();
    const user = auth.getUser();

    if (token && user) {
      set({
        user,
        token,
        isAuthenticated: true,
        isLoading: false,
      });
    } else {
      set({
        user: null,
        token: null,
        isAuthenticated: false,
        isLoading: false,
      });
    }
  },
}));
