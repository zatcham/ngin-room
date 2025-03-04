<script setup>
import { ref, onMounted } from 'vue';
import api from "@/api/axios.js";
import { useToast } from 'vue-toastification';
import RepositoryCard from './RepositoryCard.vue';

const repositories = ref([]);
const loading = ref(true);

const toast = useToast();

const fetchRepositories = async () => {
  try {
    const { data } = await api.get('/api/repos');
    repositories.value = Object.entries(data).map(([name, repo]) => ({
      name,
      ...repo
    }));
  } catch (error) {
    toast.error('Failed to fetch repositories');
    console.error('Failed to fetch repositories:', error);
  } finally {
    loading.value = false;
  }
};

onMounted(fetchRepositories);
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4">Managed Repositories</h2>

    <div v-if="loading" class="text-center py-8">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto"></div>
    </div>

    <div v-else-if="repositories.length === 0" class="text-center py-8 text-gray-500">
      No repositories found
    </div>

    <div v-else class="space-y-4">
      <RepositoryCard
        v-for="repo in repositories"
        :key="repo.name"
        :repository="repo"
        @refresh="fetchRepositories"
      />
    </div>
  </div>
</template>

<style scoped>

</style>
