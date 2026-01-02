<template>
  <div class="sticky top-0 z-10 flex h-16 flex-shrink-0 bg-white shadow">
    <div class="flex flex-1 justify-between px-4">
      <div class="flex flex-1 items-center">
        <h1 class="text-xl font-semibold text-gray-900">{{ pageTitle }}</h1>
      </div>
      <div class="ml-4 flex items-center md:ml-6">
        <!-- Current Time -->
        <div class="text-sm text-gray-500 mr-4">
          {{ currentTime }}
        </div>
        
        <!-- User Menu -->
        <div class="relative">
          <div class="flex items-center">
            <span class="hidden md:block text-sm font-medium text-gray-700 mr-2">{{ userDisplayRole }}</span>
            <div class="h-8 w-8 rounded-full bg-green-600 flex items-center justify-center">
              <span class="text-white text-sm font-medium">{{ userInitial }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute } from 'vue-router'
import { useUserStore } from '../stores/userStore'

const route = useRoute()
const { userDisplayRole, userInitial } = useUserStore()

const currentTime = ref('')

const pageTitle = computed(() => {
  const titles = {
    '/': 'Dashboard',
    '/vendors': 'Vendor Master',
    '/purchase-orders': 'Purchase Orders',
    '/inward-entry': 'Inward Entry',
    '/grn': 'GRN Approvals',
    '/control-room': 'Production Control Room',
    '/maintenance': 'Maintenance Hub',
    '/sales': 'Sales & Dispatch',
    '/reports': 'Analytics & Reports',
    '/settings/recipes': 'Recipe Manager',
    '/settings/users': 'User Management'
  }
  return titles[route.path] || 'Tyre Pyrolysis ERP'
})

const updateTime = () => {
  const now = new Date()
  currentTime.value = now.toLocaleString('en-IN', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
}

let timer
onMounted(() => {
  updateTime()
  timer = setInterval(updateTime, 60000)
})

onUnmounted(() => {
  clearInterval(timer)
})
</script>
