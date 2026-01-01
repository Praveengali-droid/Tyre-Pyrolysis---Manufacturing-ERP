<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Goods Receipt Notes</h2>
        <p class="text-sm text-gray-500">Review and approve received materials</p>
      </div>
      <router-link to="/inward-entry" class="btn btn-primary btn-lg">
        <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        New Inward Entry
      </router-link>
    </div>

    <!-- Filter Tabs -->
    <div class="flex space-x-2 mb-4">
      <button 
        @click="statusFilter = ''" 
        :class="statusFilter === '' ? 'btn-primary' : 'btn-secondary'"
        class="btn"
      >All</button>
      <button 
        @click="statusFilter = 'DRAFT'" 
        :class="statusFilter === 'DRAFT' ? 'btn-primary' : 'btn-secondary'"
        class="btn"
      >Pending Approval</button>
      <button 
        @click="statusFilter = 'APPROVED'" 
        :class="statusFilter === 'APPROVED' ? 'btn-primary' : 'btn-secondary'"
        class="btn"
      >Approved</button>
    </div>

    <!-- GRN List -->
    <div class="card overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 table-dense">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">GRN #</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Date</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vehicle</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Net Wt (kg)</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Deduction</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Payable Wt</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount (₹)</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="grn in filteredGrns" :key="grn.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-medium text-gray-900">{{ grn.grn_number }}</td>
            <td class="px-4 py-3 text-gray-600">{{ formatDate(grn.receipt_date) }}</td>
            <td class="px-4 py-3 text-gray-900 font-mono">{{ grn.vehicle_number }}</td>
            <td class="px-4 py-3 text-gray-900 font-medium">{{ grn.net_weight_kg?.toLocaleString() }}</td>
            <td class="px-4 py-3 text-red-600">-{{ grn.total_deduction_kg?.toLocaleString() }}</td>
            <td class="px-4 py-3 text-green-600 font-bold">{{ grn.payable_weight_kg?.toLocaleString() }}</td>
            <td class="px-4 py-3 text-gray-900">₹{{ grn.net_payable_amount?.toLocaleString('en-IN', {minimumFractionDigits: 2}) }}</td>
            <td class="px-4 py-3">
              <span :class="getStatusBadge(grn.status)" class="badge">{{ grn.status }}</span>
            </td>
            <td class="px-4 py-3">
              <button 
                v-if="grn.status === 'DRAFT'"
                @click="approveGrn(grn.id)"
                :disabled="approving === grn.id"
                class="btn btn-primary text-sm py-1 px-3"
              >
                {{ approving === grn.id ? 'Approving...' : '✓ Approve' }}
              </button>
              <span v-else class="text-green-600 text-sm">✓ Done</span>
            </td>
          </tr>
          
          <tr v-if="grns.length === 0 && !loading">
            <td colspan="9" class="px-4 py-8 text-center text-gray-500">
              No GRNs found. Create an inward entry first.
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Success Toast -->
    <div v-if="successMsg" class="fixed bottom-4 right-4 bg-green-500 text-white px-6 py-4 rounded-lg shadow-lg flex items-center">
      <svg class="w-6 h-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
      </svg>
      {{ successMsg }}
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { inwardApi } from '../../services/api'

const grns = ref([])
const loading = ref(false)
const approving = ref(null)
const successMsg = ref('')
const statusFilter = ref('')

const filteredGrns = computed(() => {
  if (!statusFilter.value) return grns.value
  return grns.value.filter(g => g.status === statusFilter.value)
})

const loadGrns = async () => {
  loading.value = true
  try {
    const res = await inwardApi.listGrns()
    grns.value = res.data
  } catch (e) {
    console.error('Failed to load GRNs:', e)
  } finally {
    loading.value = false
  }
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-IN')
}

const getStatusBadge = (status) => {
  const map = {
    'DRAFT': 'badge-warning',
    'APPROVED': 'badge-success',
    'REJECTED': 'badge-danger'
  }
  return map[status] || 'badge-info'
}

const approveGrn = async (grnId) => {
  approving.value = grnId
  try {
    await inwardApi.approveGrn(grnId, 'Plant Operator')
    successMsg.value = 'GRN approved! Inventory updated.'
    setTimeout(() => { successMsg.value = '' }, 3000)
    loadGrns()
  } catch (e) {
    console.error('Failed to approve GRN:', e)
    alert('Error: ' + (e.response?.data?.detail || e.message))
  } finally {
    approving.value = null
  }
}

onMounted(loadGrns)
</script>
