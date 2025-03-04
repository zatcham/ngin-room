import { defineStore } from 'pinia';
import api from '../api/axios';

export const useAuthStore = defineStore('auth', {
  state: () => ({
    isAuthenticated: false,
    user: null,
    token: localStorage.getItem('access_token') || null
  }),

  actions: {
    async login(username, password) {
      try {
        const response = await api.post('/api/login', {
          username,
          password,
        });

        const token = response.data.access_token;
        localStorage.setItem('access_token', token);
        this.token = token;
        this.isAuthenticated = true;

        // Fetch user data immediately after login
        await this.fetchUserData();

        return response;
      } catch (error) {
        this.isAuthenticated = false;
        this.token = null;
        localStorage.removeItem('access_token');
        throw error;
      }
    },

    async fetchUserData() {
      try {
        const response = await api.get('/api/protected');
        this.user = response.data.logged_in_as;
        this.isAuthenticated = true;
      } catch (error) {
        this.user = null;
        this.isAuthenticated = false;
        localStorage.removeItem('access_token');
      }
    },

    logout() {
      this.user = null;
      this.isAuthenticated = false;
      this.token = null;
      localStorage.removeItem('access_token');
    }
  }
});
