import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import api from '@/lib/api';

interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: 'student' | 'teacher' | 'admin';
  avatar_url?: string | null;
}

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
  updateUser: (user: User) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      isLoading: false,
      
      login: async (username: string, password: string) => {
        set({ isLoading: true });
        try {
          const response = await api.post('/api/auth/login', {
            username,
            password,
          });
          
          console.log('Login response:', response.data);
          
          // 后端返回的是 StandardResponse 格式，实际数据在 response.data.data 中
          const { access_token, user } = response.data.data;
          
          localStorage.setItem('token', access_token);
          localStorage.setItem('user', JSON.stringify(user));
          
          // 设置cookie用于SSR
          document.cookie = `token=${access_token}; path=/; max-age=86400`;
          
          set({
            user,
            token: access_token,
            isLoading: false,
          });
        } catch (error) {
          set({ isLoading: false });
          throw error;
        }
      },
      
      logout: () => {
        localStorage.removeItem('token');
        localStorage.removeItem('user');
        set({ user: null, token: null });
        window.location.href = '/login';
      },
      
      updateUser: (user: User) => {
        set({ user });
        localStorage.setItem('user', JSON.stringify(user));
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        token: state.token,
      }),
    }
  )
);