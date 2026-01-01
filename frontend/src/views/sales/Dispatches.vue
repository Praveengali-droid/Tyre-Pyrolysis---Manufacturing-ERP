<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">All Dispatches</h2>
        <p class="text-sm text-gray-500">View and manage all Carbon and Steel dispatches</p>
      </div>
      <div class="flex space-x-2">
        <button @click="openDispatchModal('CARBON')" class="btn btn-primary">+ Carbon Dispatch</button>
        <button @click="openDispatchModal('STEEL')" class="btn btn-warning">+ Steel Dispatch</button>
      </div>
    </div>

    <!-- Filter by type -->
    <div class="mb-4">
      <select v-model="filterType" class="input w-48">
        <option value="ALL">All Types</option>
        <option value="CARBON">Carbon Only</option>
        <option value="STEEL">Steel Only</option>
      </select>
      <select v-model="filterStatus" class="input w-48 ml-2">
        <option value="ALL">All Status</option>
        <option value="PENDING">Pending</option>
        <option value="CONFIRMED">Confirmed</option>
      </select>
    </div>

    <!-- Stats Cards -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="card p-4 text-center bg-gradient-to-br from-gray-50 to-gray-100">
        <p class="text-3xl font-bold text-gray-700">{{ totalDispatches }}</p>
        <p class="text-sm text-gray-600">Total Dispatches</p>
      </div>
      <div class="card p-4 text-center bg-gradient-to-br from-yellow-50 to-yellow-100">
        <p class="text-3xl font-bold text-yellow-700">{{ pendingCount }}</p>
        <p class="text-sm text-gray-600">Pending Confirmation</p>
      </div>
      <div class="card p-4 text-center bg-gradient-to-br from-green-50 to-green-100">
        <p class="text-3xl font-bold text-green-700">{{ confirmedCount }}</p>
        <p class="text-sm text-gray-600">Delivered / Confirmed</p>
      </div>
      <div class="card p-4 text-center bg-gradient-to-br from-blue-50 to-blue-100">
        <p class="text-2xl font-bold text-blue-700">₹{{ totalValue.toLocaleString() }}</p>
        <p class="text-sm text-gray-600">Total Value</p>
      </div>
    </div>

    <!-- Dispatches Table -->
    <div class="card">
      <div class="card-body p-0">
        <table class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left">Code</th>
              <th class="px-4 py-3 text-left">Type</th>
              <th class="px-4 py-3 text-left">Date</th>
              <th class="px-4 py-3 text-left">Qty (kg)</th>
              <th class="px-4 py-3 text-left">Rate</th>
              <th class="px-4 py-3 text-left">Amount</th>
              <th class="px-4 py-3 text-left">Vehicle</th>
              <th class="px-4 py-3 text-left">Status</th>
              <th class="px-4 py-3 text-left">Action</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="d in filteredDispatches" :key="d.type + '-' + d.id" class="border-t hover:bg-gray-50">
              <td class="px-4 py-3 font-medium">{{ d.dispatch_code }}</td>
              <td class="px-4 py-3">
                <span :class="d.type === 'CARBON' ? 'px-2 py-1 text-xs rounded bg-gray-200' : 'px-2 py-1 text-xs rounded bg-yellow-100'">
                  {{ d.type }}
                </span>
              </td>
              <td class="px-4 py-3">{{ d.dispatch_date }}</td>
              <td class="px-4 py-3">{{ d.quantity_kg }}</td>
              <td class="px-4 py-3">₹{{ d.rate_per_kg }}</td>
              <td class="px-4 py-3 text-green-600 font-medium">₹{{ d.total_amount?.toLocaleString() }}</td>
              <td class="px-4 py-3">{{ d.vehicle_number || '-' }}</td>
              <td class="px-4 py-3">
                <span v-if="d.customer_confirmed" class="text-green-600">✓ Delivered</span>
                <span v-else class="text-yellow-600">Pending</span>
              </td>
              <td class="px-4 py-3">
                <button v-if="!d.customer_confirmed" @click="confirmReceipt(d)" class="text-blue-600 hover:underline text-xs">
                  Confirm Receipt
                </button>
                <span v-else class="text-gray-400 text-xs">Completed</span>
              </td>
            </tr>
            <tr v-if="filteredDispatches.length === 0">
              <td colspan="9" class="px-4 py-8 text-center text-gray-500">No dispatches found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Dispatch Modal -->
    <div v-if="showDispatchModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showDispatchModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">{{ dispatchType }} Dispatch</h3>
          <form @submit.prevent="createDispatch" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Customer *</label>
              <select v-model="dispatchForm.customer_id" required class="mt-1 input">
                <option value="">-- Select Customer --</option>
                <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }} ({{ c.customer_code }})</option>
              </select>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Quantity (kg) *</label>
                <input v-model.number="dispatchForm.quantity_kg" type="number" required min="1" class="mt-1 input">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Rate (₹/kg) *</label>
                <input v-model.number="dispatchForm.rate_per_kg" type="number" required min="0" step="0.01" class="mt-1 input">
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Vehicle Number</label>
              <input v-model="dispatchForm.vehicle_number" type="text" class="mt-1 input">
            </div>
            <div class="bg-green-50 p-3 rounded-lg">
              <p class="text-lg font-bold text-green-700">Total: ₹{{ (dispatchForm.quantity_kg * dispatchForm.rate_per_kg).toLocaleString() }}</p>
            </div>
            <div class="flex justify-end space-x-3">
              <button type="button" @click="showDispatchModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Creating...' : 'Create Dispatch' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { salesApi } from '../../services/api'

const carbonDispatches = ref([])
const steelDispatches = ref([])
const customers = ref([])
const filterType = ref('ALL')
const filterStatus = ref('ALL')
const showDispatchModal = ref(false)
const dispatchType = ref('CARBON')
const saving = ref(false)
const dispatchForm = ref({ customer_id: '', quantity_kg: 100, rate_per_kg: 15, vehicle_number: '' })

// Combine all dispatches
const allDispatches = computed(() => {
  const carbon = carbonDispatches.value.map(d => ({ ...d, type: 'CARBON' }))
  const steel = steelDispatches.value.map(d => ({ ...d, type: 'STEEL' }))
  return [...carbon, ...steel].sort((a, b) => new Date(b.dispatch_date) - new Date(a.dispatch_date))
})

const filteredDispatches = computed(() => {
  return allDispatches.value.filter(d => {
    if (filterType.value !== 'ALL' && d.type !== filterType.value) return false
    if (filterStatus.value === 'PENDING' && d.customer_confirmed) return false
    if (filterStatus.value === 'CONFIRMED' && !d.customer_confirmed) return false
    return true
  })
})

const totalDispatches = computed(() => allDispatches.value.length)
const pendingCount = computed(() => allDispatches.value.filter(d => !d.customer_confirmed).length)
const confirmedCount = computed(() => allDispatches.value.filter(d => d.customer_confirmed).length)
const totalValue = computed(() => allDispatches.value.reduce((sum, d) => sum + (d.total_amount || 0), 0))

const loadData = async () => {
  try {
    const [carbonRes, steelRes, customersRes] = await Promise.all([
      salesApi.listCarbonDispatches(),
      salesApi.listSteelDispatches(),
      salesApi.listCustomers()
    ])
    carbonDispatches.value = carbonRes.data
    steelDispatches.value = steelRes.data
    customers.value = customersRes.data
  } catch (e) {
    console.error('Failed to load data:', e)
  }
}

const openDispatchModal = (type) => {
  dispatchType.value = type
  dispatchForm.value = { customer_id: '', quantity_kg: 100, rate_per_kg: type === 'CARBON' ? 15 : 25, vehicle_number: '' }
  showDispatchModal.value = true
}

const createDispatch = async () => {
  saving.value = true
  try {
    if (dispatchType.value === 'CARBON') {
      await salesApi.createCarbonDispatch(dispatchForm.value)
    } else {
      await salesApi.createSteelDispatch(dispatchForm.value)
    }
    showDispatchModal.value = false
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const confirmReceipt = async (dispatch) => {
  try {
    if (dispatch.type === 'CARBON') {
      await salesApi.confirmCarbonReceipt(dispatch.id)
    } else {
      await salesApi.confirmSteelReceipt(dispatch.id)
    }
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(loadData)
</script>
