<template>
  <div class="min-h-screen flex items-center justify-center bg-gray-900">
    <div class="max-w-md w-full bg-white rounded-lg shadow-xl p-8">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="w-16 h-16 bg-blue-600 rounded-full mx-auto flex items-center justify-center mb-4">
          <svg class="w-10 h-10 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17.657 18.657A8 8 0 016.343 7.343S7 9 9 10c0-2 .5-5 2.986-7C14 5 16.09 5.777 17.656 7.343A7.975 7.975 0 0120 13a7.975 7.975 0 01-2.343 5.657z" />
          </svg>
        </div>
        <h1 class="text-2xl font-bold text-gray-900">Pyrolysis ERP</h1>
        <p class="text-gray-500 mt-1">Sign in to continue</p>
      </div>

      <!-- Error Alert -->
      <div v-if="error" class="mb-4 p-3 bg-red-100 border border-red-300 text-red-700 rounded text-sm">
        {{ error }}
      </div>

      <!-- Login Form -->
      <form @submit.prevent="handleLogin" class="space-y-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Username</label>
          <input 
            v-model="username" 
            type="text" 
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter username"
            required
          >
        </div>

        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">Password</label>
          <input 
            v-model="password" 
            type="password" 
            class="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
            placeholder="Enter password"
            required
          >
        </div>

        <button 
          type="submit" 
          :disabled="loading"
          class="w-full py-3 px-4 bg-blue-600 hover:bg-blue-700 text-white font-medium rounded-lg transition disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {{ loading ? 'Signing in...' : 'Sign In' }}
        </button>
      </form>

      <!-- Help Text -->
      <p class="mt-6 text-center text-sm text-gray-500">
        Manufacturing ERP System v1.0
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '../services/api'
import { useUserStore } from '../stores/userStore'

const router = useRouter()
const { setUser } = useUserStore()

const username = ref('')
const password = ref('')
const loading = ref(false)
const error = ref('')

// Role-based landing pages
const getRoleLandingPage = (role) => {
  switch (role) {
    case 'ADMIN':
      return '/reports'  // Admins want to see business intelligence first
    case 'MANAGER':
      return '/sales'    // Managers want to see sales pipeline
    case 'OPERATOR':
      return '/control-room'  // Operators want to see active reactors
    case 'VIEWER':
    default:
      return '/'  // Default dashboard for viewers
  }
}

const handleLogin = async () => {
  error.value = ''
  loading.value = true

  try {
    const response = await authApi.login(username.value, password.value)
    const { access_token, user } = response.data

    // Store token and user info in reactive store
    setUser(user, access_token)

    // Role-based redirect
    const landingPage = getRoleLandingPage(user.role)
    router.push(landingPage)
  } catch (e) {
    error.value = e.response?.data?.detail || 'Login failed. Please check your credentials.'
  } finally {
    loading.value = false
  }
}
</script>
