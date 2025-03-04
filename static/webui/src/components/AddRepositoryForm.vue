<script setup>
import { ref } from 'vue';
import api from '@/api/axios';
import { useToast }  from 'vue-toastification';

const showForm = ref(false);
const formData = ref({
  name: '',
  git_url: '',
  domain: '',
  nginx_config: ''
});

const toast = useToast();

const emit = defineEmits(['repository-added']);

const handleSubmit = async () => {
  try {
    await api.post('/api/repos', formData.value);
    toast.success('Repository added successfully');
    emit('repository-added');
    showForm.value = false;
    formData.value = { name: '', git_url: '', domain: '', nginx_config: '' };
  } catch (error) {
    toast.error('Failed to add repository');
    console.error('Failed to add repository:', error);
  }
};
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <div class="flex justify-between items-center mb-4">
      <h2 class="text-xl font-bold">Add New Repository</h2>
      <button
        @click="showForm = !showForm"
        class="bg-blue-500 text-white px-4 py-2 rounded hover:bg-blue-600"
      >
        {{ showForm ? 'Cancel' : 'Add Repository' }}
      </button>
    </div>

    <form v-if="showForm" @submit.prevent="handleSubmit" class="space-y-4">
      <div>
        <label class="block text-sm font-medium mb-1">Repository Name</label>
        <input
          v-model="formData.name"
          type="text"
          required
          class="w-full p-2 border rounded"
        >
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">Git URL</label>
        <input
          v-model="formData.git_url"
          type="text"
          required
          class="w-full p-2 border rounded"
        >
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">Domain</label>
        <input
          v-model="formData.domain"
          type="text"
          required
          class="w-full p-2 border rounded"
        >
      </div>
      <div>
        <label class="block text-sm font-medium mb-1">Nginx Configuration (Optional)</label>
        <textarea
          v-model="formData.nginx_config"
          rows="6"
          class="w-full p-2 border rounded font-mono text-sm"
          placeholder="server {
    listen 80;
    server_name example.com;
    root /var/www/example/public;
    location / {
        try_files $uri $uri/ /index.html;
    }
}"
        ></textarea>
      </div>
      <button
        type="submit"
        class="bg-green-500 text-white px-4 py-2 rounded hover:bg-green-600"
      >
        Add Repository
      </button>
    </form>
  </div>
</template>

<style scoped>

</style>
