<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">User Management</h2>
        <p class="text-sm text-gray-500">Manage system users and roles</p>
      </div>
      <button @click="showCreateModal = true" class="btn btn-primary">+ Add User</button>
    </div>

    <!-- Users Table -->
    <div class="card">
      <div class="card-body p-0">
        <table class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left">Username</th>
              <th class="px-4 py-3 text-left">Full Name</th>
              <th class="px-4 py-3 text-left">Email</th>
              <th class="px-4 py-3 text-left">Role</th>
              <th class="px-4 py-3 text-left">Status</th>
              <th class="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in users" :key="user.id" class="border-t hover:bg-gray-50">
              <td class="px-4 py-3 font-medium">{{ user.username }}</td>
              <td class="px-4 py-3">{{ user.full_name || '-' }}</td>
              <td class="px-4 py-3 text-gray-500">{{ user.email || '-' }}</td>
              <td class="px-4 py-3">
                <span :class="getRoleBadge(user.role)">{{ user.role }}</span>
              </td>
              <td class="px-4 py-3">
                <span :class="user.is_active ? 'text-green-600' : 'text-red-600'">
                  {{ user.is_active ? 'Active' : 'Inactive' }}
                </span>
              </td>
              <td class="px-4 py-3 space-x-2">
                <button @click="openResetPassword(user)" class="text-blue-600 hover:underline text-xs">Reset Password</button>
                <button v-if="user.is_active" @click="deactivate(user)" class="text-red-600 hover:underline text-xs">Deactivate</button>
                <button v-else @click="activate(user)" class="text-green-600 hover:underline text-xs">Activate</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create User Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showCreateModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 class="text-lg font-medium mb-4">Create User</h3>
          <form @submit.prevent="createUser" class="space-y-4">
            <div>
              <label class="block text-sm text-gray-600">Username *</label>
              <input v-model="form.username" type="text" class="input w-full" required>
            </div>
            <div>
              <label class="block text-sm text-gray-600">Password *</label>
              <input v-model="form.password" type="password" class="input w-full" required>
            </div>
            <div>
              <label class="block text-sm text-gray-600">Full Name</label>
              <input v-model="form.full_name" type="text" class="input w-full">
            </div>
            <div>
              <label class="block text-sm text-gray-600">Email</label>
              <input v-model="form.email" type="email" class="input w-full">
            </div>
            <div>
              <label class="block text-sm text-gray-600">Role</label>
              <select v-model="form.role" class="input w-full">
                <option value="ADMIN">ADMIN</option>
                <option value="MANAGER">MANAGER</option>
                <option value="OPERATOR">OPERATOR</option>
                <option value="VIEWER">VIEWER</option>
              </select>
            </div>
            <div class="flex justify-end space-x-3">
              <button type="button" @click="showCreateModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Creating...' : 'Create' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Reset Password Modal -->
    <div v-if="showResetModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showResetModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 class="text-lg font-medium mb-4">Reset Password - {{ selectedUser?.username }}</h3>
          <form @submit.prevent="resetPassword" class="space-y-4">
            <div>
              <label class="block text-sm text-gray-600">New Password *</label>
              <input v-model="newPassword" type="password" class="input w-full" required>
            </div>
            <div class="flex justify-end space-x-3">
              <button type="button" @click="showResetModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">Reset</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { authApi } from '../../services/api'

const users = ref([])
const showCreateModal = ref(false)
const showResetModal = ref(false)
const selectedUser = ref(null)
const newPassword = ref('')
const saving = ref(false)
const form = ref({ username: '', password: '', full_name: '', email: '', role: 'OPERATOR' })

const loadUsers = async () => {
  try {
    const res = await authApi.listUsers()
    users.value = res.data
  } catch (e) { console.error(e) }
}

const getRoleBadge = (role) => ({
  ADMIN: 'px-2 py-0.5 text-xs rounded bg-red-100 text-red-700',
  MANAGER: 'px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-700',
  OPERATOR: 'px-2 py-0.5 text-xs rounded bg-green-100 text-green-700',
  VIEWER: 'px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-600'
}[role] || '')

const createUser = async () => {
  saving.value = true
  try {
    await authApi.createUser(form.value)
    showCreateModal.value = false
    form.value = { username: '', password: '', full_name: '', email: '', role: 'OPERATOR' }
    loadUsers()
  } catch (e) { alert('Error: ' + (e.response?.data?.detail || e.message)) }
  finally { saving.value = false }
}

const openResetPassword = (user) => { selectedUser.value = user; newPassword.value = ''; showResetModal.value = true }

const resetPassword = async () => {
  saving.value = true
  try {
    await authApi.resetPassword(selectedUser.value.id, newPassword.value)
    showResetModal.value = false
    alert('Password reset successfully')
  } catch (e) { alert('Error: ' + e.message) }
  finally { saving.value = false }
}

const deactivate = async (user) => {
  if (!confirm(`Deactivate ${user.username}?`)) return
  try {
    await authApi.deactivateUser(user.id)
    loadUsers()
  } catch (e) { alert('Error: ' + e.message) }
}

const activate = async (user) => {
  try {
    await authApi.activateUser(user.id)
    loadUsers()
  } catch (e) { alert('Error: ' + e.message) }
}

onMounted(loadUsers)
</script>
