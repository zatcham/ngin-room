<script setup>
import { ref } from 'vue';
import api from '@/api/axios';
import { useToast } from 'vue-toastification';
import {
  Power,
  GitPullRequest,
  Copy,
  Edit,
  Trash,
  AlertCircle,
  TerminalSquare
} from 'lucide-vue-next';

const props = defineProps({
  repository: {
    type: Object,
    required: true
  }
});

const toast = useToast();
const emit = defineEmits(['refresh']);

const showNginxConfig = ref(false);
const showLogs = ref(false);
const editingConfig = ref(false);
const showDuplicateForm = ref(false);
const logs = ref(null);
const nginxConfig = ref(props.repository.nginx_config);
const duplicateForm = ref({
  new_name: '',
  new_domain: '',
  new_path: ''
});

const toggleSite = async () => {
  try {
    await api.post(`/api/repos/${props.repository.name}/toggle`);
    toast.success(`Site ${props.repository.enabled ? 'disabled' : 'enabled'}`);
    emit('refresh');
  } catch (error) {
    toast.error('Failed to toggle site status');
  }
};

const pullRepository = async () => {
  try {
    await api.post(`/api/repos/${props.repository.name}/pull`);
    toast.success('Repository pulled successfully');
  } catch (error) {
    toast.error('Failed to pull repository');
  }
};

const saveNginxConfig = async () => {
  try {
    await api.put(`/api/repos/${props.repository.name}/config`, {
      nginx_config: nginxConfig.value
    });
    toast.success('Nginx configuration updated');
    editingConfig.value = false;
    emit('refresh');
  } catch (error) {
    toast.error('Failed to update Nginx configuration');
  }
};

const duplicateRepository = async () => {
  try {
    await api.post(`/api/repos/${props.repository.name}/duplicate`, duplicateForm.value);
    toast.success('Repository duplicated successfully');
    showDuplicateForm.value = false;
    duplicateForm.value = { new_name: '', new_domain: '', new_path: '' };
    emit('refresh');
  } catch (error) {
    toast.error('Failed to duplicate repository');
  }
};

const fetchLogs = async () => {
  try {
    const { data } = await api.get(`/api/logs/${props.repository.name}`);
    logs.value = data;
    showLogs.value = true;
  } catch (error) {
    toast.error('Failed to fetch logs');
  }
};
</script>

<template>
  <div class="border rounded-lg p-4 hover:shadow-md transition-shadow">
    <div class="flex justify-between items-start">
      <div>
        <h3 class="text-lg font-bold">{{ repository.name }}</h3>
        <p class="text-sm text-gray-600">{{ repository.domain }}</p>
        <p class="text-xs text-gray-500">{{ repository.git_url }}</p>
      </div>

      <div class="flex space-x-2">
        <button
          @click="toggleSite"
          :class="[
            'p-2 rounded',
            repository.enabled ? 'text-green-500' : 'text-gray-500'
          ]"
          :title="repository.enabled ? 'Disable Site' : 'Enable Site'"
        >
          <Power />
        </button>

        <button
          @click="pullRepository"
          class="p-2 rounded text-blue-500"
          title="Pull Latest Changes"
        >
          <GitPullRequest />
        </button>

        <button
          @click="showDuplicateForm = true"
          class="p-2 rounded text-purple-500"
          title="Duplicate Site"
        >
          <Copy />
        </button>

        <button
          @click="showNginxConfig = true"
          class="p-2 rounded text-orange-500"
          title="View/Edit Nginx Config"
        >
          <Edit />
        </button>

        <button
          @click="fetchLogs"
          class="p-2 rounded text-gray-500"
          title="View Logs"
        >
          <TerminalSquare />
        </button>
      </div>
    </div>

    <!-- Nginx Config Modal -->
    <div v-if="showNginxConfig" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg p-6 max-w-2xl w-full">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold">Nginx Configuration</h3>
          <button
            @click="showNginxConfig = false"
            class="text-gray-500 hover:text-gray-700"
          >
            ×
          </button>
        </div>

        <textarea
          v-model="nginxConfig"
          rows="15"
          :readonly="!editingConfig"
          class="w-full p-2 border rounded font-mono text-sm mb-4"
        ></textarea>

        <div class="flex justify-end space-x-2">
          <button
            v-if="!editingConfig"
            @click="editingConfig = true"
            class="bg-blue-500 text-white px-4 py-2 rounded"
          >
            Edit
          </button>
          <button
            v-else
            @click="saveNginxConfig"
            class="bg-green-500 text-white px-4 py-2 rounded"
          >
            Save
          </button>
          <button
            @click="showNginxConfig = false"
            class="bg-gray-500 text-white px-4 py-2 rounded"
          >
            Close
          </button>
        </div>
      </div>
    </div>

    <!-- Duplicate Form Modal -->
    <div v-if="showDuplicateForm" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4">
      <div class="bg-white rounded-lg p-6 max-w-md w-full">
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-bold">Duplicate Repository</h3>
          <button
            @click="showDuplicateForm = false"
            class="text-gray-500 hover:text-gray-700"
          >
            ×
          </button>
        </div>

        <form @submit.prevent="duplicateRepository" class="space-y-4">
          <div>
            <label class="block text-sm font-medium mb-1">New Name</label>
            <input
              v-model="duplicateForm.new_name"
              type="text"
              required
              class="w-full p-2 border rounded"
            >
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">New Domain</label>
            <input
              v-model="duplicateForm.new_domain"
              type="text"
              required
              class="w-full p-2 border rounded"
            >
          </div>
          <div>
            <label class="block text-sm font-medium mb-1">New Path</label>
            <input
              v-model="duplicateForm.new_path"
              type="text"
              required
              class="w-full p-2 border rounded"
              >
          </div>
          <div class="flex justify-end space-x-2">
            <button
              type="submit"
              class="bg-blue-500 text-white px-4 py-2 rounded"
            >
              Duplicate
            </button>
            <button
              @click="showDuplicateForm = false"
              class="bg-gray-500 text-white px-4 py-2 rounded"
            >
              Cancel
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>
