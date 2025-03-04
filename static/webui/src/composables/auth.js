import { ref, computed } from 'vue';
import { useAuthStore } from '../stores/auth';

// Composable wrapper for the store
export function useAuth() {
  const store = useAuthStore();

  // Initialize auth state on app load
  const initAuth = async () => {
    if (store.token) {
      await store.fetchUserData();
    }
  };

  return {
    isAuthenticated: computed(() => store.isAuthenticated),
    user: computed(() => store.user),
    login: store.login,
    logout: store.logout,
    initAuth
  };
}
