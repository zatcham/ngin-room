<script setup>
import { ref, onMounted, onUnmounted } from 'vue';
import api from "@/api/axios.js";
import { ArrowUpCircle, CpuIcon, HardDrive } from 'lucide-vue-next';

const stats = ref({
  cpu_usage: 0,
  memory_usage: 0,
  disk_usage: 0,
  uptime: ''
});

let interval;

const fetchStats = async () => {
  try {
    const { data } = await api.get('/api/stats');
    stats.value = data;
  } catch (error) {
    console.error('Failed to fetch server stats:', error);
  }
};

onMounted(() => {
  fetchStats();
  interval = setInterval(fetchStats, 30000); // Update every 30 seconds
});

onUnmounted(() => {
  clearInterval(interval);
});
</script>

<template>
  <div class="bg-white p-6 rounded-lg shadow-md">
    <h2 class="text-xl font-bold mb-4">Server Status</h2>
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4">
      <div class="p-4 bg-gray-50 rounded-lg">
        <div class="flex items-center space-x-2">
          <CpuIcon class="text-blue-500" />
          <span class="font-medium">CPU Usage</span>
        </div>
        <div class="text-2xl font-bold mt-2">{{ stats.cpu_usage }}%</div>
      </div>
      <div class="p-4 bg-gray-50 rounded-lg">
        <div class="flex items-center space-x-2">
<!--          <Memory class="text-green-500" />-->
          <span class="font-medium">Memory Usage</span>
        </div>
        <div class="text-2xl font-bold mt-2">{{ stats.memory_usage }}%</div>
      </div>
      <div class="p-4 bg-gray-50 rounded-lg">
        <div class="flex items-center space-x-2">
          <HardDrive class="text-purple-500" />
          <span class="font-medium">Disk Usage</span>
        </div>
        <div class="text-2xl font-bold mt-2">{{ stats.disk_usage }}%</div>
      </div>
      <div class="p-4 bg-gray-50 rounded-lg">
        <div class="flex items-center space-x-2">
          <ArrowUpCircle class="text-yellow-500" />
          <span class="font-medium">Uptime</span>
        </div>
        <div class="text-lg font-bold mt-2">{{ stats.uptime }}</div>
      </div>
    </div>
  </div>
</template>

<style scoped>

</style>
