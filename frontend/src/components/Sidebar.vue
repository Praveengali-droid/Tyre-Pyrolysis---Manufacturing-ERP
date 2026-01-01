<template>
  <!-- Sidebar for desktop -->
  <div class="hidden lg:fixed lg:inset-y-0 lg:flex lg:w-64 lg:flex-col">
    <div class="flex min-h-0 flex-1 flex-col bg-gray-800">
      <!-- Logo -->
      <div class="flex h-16 flex-shrink-0 items-center px-4 bg-gray-900">
        <div class="flex items-center">
          <div class="w-8 h-8 bg-green-500 rounded-lg flex items-center justify-center">
            <span class="text-white font-bold text-lg">T</span>
          </div>
          <span class="ml-3 text-white font-semibold text-lg">Tyre Pyrolysis ERP</span>
        </div>
      </div>
      
      <!-- Navigation -->
      <div class="flex flex-1 flex-col overflow-y-auto">
        <nav class="flex-1 space-y-1 px-2 py-4">
          <!-- Dashboard -->
          <router-link
            to="/"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6" />
            </svg>
            Dashboard
          </router-link>
          
          <!-- Procurement Section -->
          <div class="pt-4">
            <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Procurement
            </p>
          </div>
          
          <router-link
            to="/vendors"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/vendors' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
            </svg>
            Vendor Master
          </router-link>
          
          <router-link
            to="/purchase-orders"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/purchase-orders' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Purchase Orders
          </router-link>
          
          <router-link
            to="/inward-entry"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/inward-entry' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 4H6a2 2 0 00-2 2v12a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-2m-4-1v8m0 0l3-3m-3 3L9 8m-5 5h2.586a1 1 0 01.707.293l2.414 2.414a1 1 0 00.707.293h3.172a1 1 0 00.707-.293l2.414-2.414a1 1 0 01.707-.293H20" />
            </svg>
            Inward Entry
          </router-link>
          
          <router-link
            to="/grn"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/grn' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            GRN Approvals
          </router-link>
          
          <!-- Production Section -->
          <div class="pt-4">
            <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Production
            </p>
          </div>
          
          <router-link
            to="/control-room"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/control-room' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 3v2m6-2v2M9 19v2m6-2v2M5 9H3m2 6H3m18-6h-2m2 6h-2M7 19h10a2 2 0 002-2V7a2 2 0 00-2-2H7a2 2 0 00-2 2v10a2 2 0 002 2zM9 9h6v6H9V9z" />
            </svg>
            Control Room
          </router-link>
          
          <router-link
            to="/maintenance"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/maintenance' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
            Maintenance Hub
          </router-link>
          
          <!-- Sales Section -->
          <div class="pt-4">
            <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Sales
            </p>
          </div>
          
          <router-link
            to="/sales"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/sales' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            Dispatch & Sales
          </router-link>
          
          <router-link
            to="/sales/quotations"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md pl-10"
            :class="$route.path === '/sales/quotations' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
            </svg>
            Quotations
          </router-link>
          
          <router-link
            to="/sales/orders"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md pl-10"
            :class="$route.path === '/sales/orders' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-6 9l2 2 4-4" />
            </svg>
            Sale Orders
          </router-link>
          
          <router-link
            to="/sales/returns"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md pl-10"
            :class="$route.path === '/sales/returns' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 10h10a8 8 0 018 8v2M3 10l6 6m-6-6l6-6" />
            </svg>
            Sales Returns
          </router-link>
          
          <!-- Reports Section (Manager+) -->
          <div v-if="canAccessReports" class="pt-4">
            <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Reports
            </p>
          </div>
          
          <router-link
            v-if="canAccessReports"
            to="/reports"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/reports' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
            </svg>
            Analytics & Reports
          </router-link>
          
          <!-- Settings Section -->
          <div class="pt-4">
            <p class="px-3 text-xs font-semibold text-gray-400 uppercase tracking-wider">
              Settings
            </p>
          </div>
          
          <router-link
            to="/settings/recipes"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/settings/recipes' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2m-3 7h3m-3 4h3m-6-4h.01M9 16h.01" />
            </svg>
            Recipe Manager
          </router-link>
          
          <router-link
            v-if="isAdmin"
            to="/settings/users"
            class="group flex items-center px-3 py-2 text-sm font-medium rounded-md"
            :class="$route.path === '/settings/users' ? 'bg-gray-900 text-white' : 'text-gray-300 hover:bg-gray-700 hover:text-white'"
          >
            <svg class="mr-3 h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
            </svg>
            User Management
          </router-link>
        </nav>
      </div>
      
      <!-- User Profile & Logout -->
      <div class="flex-shrink-0 bg-gray-700 p-4">
        <div class="flex items-center justify-between">
          <div class="flex items-center">
            <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center text-white font-medium">
              {{ userInitial }}
            </div>
            <div class="ml-3">
              <p class="text-sm font-medium text-white">{{ userName }}</p>
              <p class="text-xs text-gray-400">{{ userRole }}</p>
            </div>
          </div>
          <button @click="logout" class="text-gray-400 hover:text-white" title="Logout">
            <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 16l4-4m0 0l-4-4m4 4H7m6 4v1a3 3 0 01-3 3H6a3 3 0 01-3-3V7a3 3 0 013-3h4a3 3 0 013 3v1" />
            </svg>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { authApi } from '../services/api'

const user = computed(() => JSON.parse(localStorage.getItem('user') || '{}'))
const userName = computed(() => user.value.full_name || user.value.username || 'User')
const userRole = computed(() => user.value.role || 'OPERATOR')
const userInitial = computed(() => (user.value.username || 'U')[0].toUpperCase())
const isAdmin = computed(() => user.value.role === 'ADMIN')
const canAccessReports = computed(() => ['ADMIN', 'MANAGER'].includes(user.value.role))

const logout = () => {
  authApi.logout()
}
</script>
