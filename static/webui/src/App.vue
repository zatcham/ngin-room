<script setup>
import { ref, onMounted } from 'vue';
import { useAuth } from './composables/auth';
import LoginForm from './components/LoginForm.vue';
import ServerStats from './components/ServerStats.vue';
import RepositoryList from './components/RepositoryList.vue';
import AddRepositoryForm from './components/AddRepositoryForm.vue';

const { isAuthenticated, initAuth } = useAuth();

// Initialize authentication state when the app loads
onMounted(async () => {
  await initAuth();
});
</script>

<template>
  <div class="min-h-screen bg-gray-100">
    <template v-if="!isAuthenticated">
      <LoginForm class="max-w-md mx-auto mt-20" />
    </template>
    <template v-else>
      <div class="container mx-auto px-4 py-8">
        <h1 class="text-3xl font-bold mb-8">Deployment Manager</h1>
        <ServerStats class="mb-8" />
        <AddRepositoryForm class="mb-8" />
        <RepositoryList />
      </div>
    </template>
  </div>
</template>
