<template>
  <div>
    <!-- Header with Tabs -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Maintenance Hub</h2>
        <p class="text-sm text-gray-500">Reactor maintenance, safety interlocks, and work requests</p>
      </div>
      <button @click="showRequestModal = true" class="btn btn-primary">+ Create Request</button>
    </div>

    <!-- Tab Navigation -->
    <div class="border-b mb-6">
      <nav class="flex space-x-8">
        <button @click="activeTab = 'reactors'" :class="activeTab === 'reactors' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'" class="py-2 px-1 border-b-2 font-medium text-sm">
          Reactor Status
        </button>
        <button @click="activeTab = 'requests'" :class="activeTab === 'requests' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'" class="py-2 px-1 border-b-2 font-medium text-sm">
          Requests <span v-if="requestSummary.total_active" class="ml-1 px-2 py-0.5 text-xs bg-red-100 text-red-600 rounded-full">{{ requestSummary.total_active }}</span>
        </button>
        <button @click="activeTab = 'logs'" :class="activeTab === 'logs' ? 'border-blue-500 text-blue-600' : 'border-transparent text-gray-500 hover:text-gray-700'" class="py-2 px-1 border-b-2 font-medium text-sm">
          History
        </button>
      </nav>
    </div>

    <!-- Tab: Reactor Status -->
    <div v-if="activeTab === 'reactors'">
      <!-- Summary Cards -->
      <div class="grid grid-cols-3 gap-6 mb-6">
        <div class="card p-4 bg-red-50 border-red-200">
          <p class="text-3xl font-bold text-red-600">{{ dueTasks.length }}</p>
          <p class="text-sm text-red-700 font-medium">🔒 BLOCKED</p>
        </div>
        <div class="card p-4 bg-yellow-50 border-yellow-200">
          <p class="text-3xl font-bold text-yellow-600">{{ warningTasks.length }}</p>
          <p class="text-sm text-yellow-700 font-medium">⚠️ Warning</p>
        </div>
        <div class="card p-4 bg-green-50 border-green-200">
          <p class="text-3xl font-bold text-green-600">{{ okReactors }}</p>
          <p class="text-sm text-green-700 font-medium">✅ OK</p>
        </div>
      </div>

      <!-- Reactor Cards -->
      <div class="grid grid-cols-4 gap-4 mb-6">
        <div v-for="r in reactorStatus" :key="r.reactor_id" :class="getCardClass(r)" class="card p-4 cursor-pointer hover:shadow-lg transition" @click="openCompleteModal(r)">
          <div class="flex justify-between items-start mb-2">
            <span class="text-xl font-bold">{{ r.reactor_code }}</span>
            <span :class="getStatusBadge(r.maintenance_status)" class="text-xs px-2 py-0.5 rounded-full">{{ r.maintenance_status }}</span>
          </div>
          <!-- Breakdown Alert -->
          <div v-if="r.active_breakdown" class="mt-2 p-2 bg-red-200 rounded text-xs text-red-800">
            ⚠️ <strong>{{r.active_breakdown.priority}}</strong>: {{ r.active_breakdown.title }}
          </div>
          <div class="mt-3">
            <div class="flex justify-between text-xs text-gray-500 mb-1">
              <span>Batches</span>
              <span>{{ r.batches_since_cleaning }} / {{ r.maintenance_frequency }}</span>
            </div>
            <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
              <div :style="{ width: getProgressWidth(r) }" :class="getProgressColor(r)" class="h-full rounded-full"></div>
            </div>
          </div>
          <button v-if="r.maintenance_status !== 'OK'" @click.stop="openCompleteModal(r)" class="mt-3 text-xs text-blue-600 hover:underline">Complete Cleaning</button>
        </div>
      </div>
    </div>

    <!-- Tab: Requests -->
    <div v-if="activeTab === 'requests'">
      <!-- Request Summary -->
      <div class="grid grid-cols-5 gap-4 mb-6">
        <div @click="requestFilter = ''" :class="requestFilter === '' ? 'ring-2 ring-blue-500' : ''" class="card p-3 text-center cursor-pointer">
          <p class="text-2xl font-bold">{{ requests.length }}</p>
          <p class="text-xs text-gray-500">All</p>
        </div>
        <div @click="requestFilter = 'OPEN'" :class="requestFilter === 'OPEN' ? 'ring-2 ring-yellow-500' : ''" class="card p-3 text-center cursor-pointer bg-yellow-50">
          <p class="text-2xl font-bold text-yellow-600">{{ requestSummary.open }}</p>
          <p class="text-xs text-gray-500">Open</p>
        </div>
        <div @click="requestFilter = 'IN_PROGRESS'" :class="requestFilter === 'IN_PROGRESS' ? 'ring-2 ring-blue-500' : ''" class="card p-3 text-center cursor-pointer bg-blue-50">
          <p class="text-2xl font-bold text-blue-600">{{ requestSummary.in_progress }}</p>
          <p class="text-xs text-gray-500">In Progress</p>
        </div>
        <div @click="requestFilter = 'ON_HOLD'" :class="requestFilter === 'ON_HOLD' ? 'ring-2 ring-orange-500' : ''" class="card p-3 text-center cursor-pointer bg-orange-50">
          <p class="text-2xl font-bold text-orange-600">{{ requestSummary.on_hold }}</p>
          <p class="text-xs text-gray-500">On Hold</p>
        </div>
        <div @click="requestFilter = 'COMPLETED'" :class="requestFilter === 'COMPLETED' ? 'ring-2 ring-green-500' : ''" class="card p-3 text-center cursor-pointer bg-green-50">
          <p class="text-2xl font-bold text-green-600">{{ requestSummary.completed }}</p>
          <p class="text-xs text-gray-500">Completed</p>
        </div>
      </div>

      <!-- Request Table -->
      <div class="card">
        <div class="card-body p-0">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left">REQ #</th>
                <th class="px-4 py-3 text-left">Title</th>
                <th class="px-4 py-3 text-left">Equipment</th>
                <th class="px-4 py-3 text-left">Type</th>
                <th class="px-4 py-3 text-left">Priority</th>
                <th class="px-4 py-3 text-left">Status</th>
                <th class="px-4 py-3 text-left">Requested</th>
                <th class="px-4 py-3 text-left">Actions</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="req in filteredRequests" :key="req.id" class="border-t hover:bg-gray-50">
                <td class="px-4 py-3 font-medium text-blue-600">{{ req.request_number }}</td>
                <td class="px-4 py-3">{{ req.title }}</td>
                <td class="px-4 py-3">{{ req.equipment_name || req.equipment_type }}</td>
                <td class="px-4 py-3"><span :class="getTypeBadge(req.request_type)">{{ req.request_type }}</span></td>
                <td class="px-4 py-3"><span :class="getPriorityBadge(req.priority)">{{ req.priority }}</span></td>
                <td class="px-4 py-3"><span :class="getReqStatusBadge(req.status)">{{ req.status.replace('_', ' ') }}</span></td>
                <td class="px-4 py-3 text-gray-500">{{ formatDate(req.requested_at) }}</td>
                <td class="px-4 py-3 space-x-1">
                  <button v-if="req.status === 'OPEN'" @click="markInProgress(req)" class="text-xs text-blue-600 hover:underline">Start</button>
                  <button v-if="['OPEN', 'IN_PROGRESS'].includes(req.status)" @click="openCompleteRequestModal(req)" class="text-xs text-green-600 hover:underline">Complete</button>
                </td>
              </tr>
              <tr v-if="filteredRequests.length === 0">
                <td colspan="8" class="px-4 py-8 text-center text-gray-500">No requests found</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Tab: Logs/History -->
    <div v-if="activeTab === 'logs'">
      <div class="card">
        <div class="card-header bg-gray-50 border-b px-4 py-3">
          <h3 class="font-medium">Maintenance Logs</h3>
        </div>
        <div class="card-body p-0">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-2 text-left">Date</th>
                <th class="px-4 py-2 text-left">Reactor</th>
                <th class="px-4 py-2 text-left">Performed By</th>
                <th class="px-4 py-2 text-left">Notes</th>
                <th class="px-4 py-2 text-left">Batches Reset</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="log in logs" :key="log.id" class="border-t">
                <td class="px-4 py-3">{{ formatDate(log.performed_date) }}</td>
                <td class="px-4 py-3 font-medium">{{ getReactorCode(log.reactor_id) }}</td>
                <td class="px-4 py-3">{{ log.performed_by }}</td>
                <td class="px-4 py-3 text-gray-600">{{ log.notes || '-' }}</td>
                <td class="px-4 py-3 text-green-600">{{ log.batches_at_maintenance }} → 0</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- Create Request Modal -->
    <div v-if="showRequestModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showRequestModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Create Maintenance Request</h3>
          <form @submit.prevent="createRequest" class="space-y-4">
            <div>
              <label class="block text-sm text-gray-600">Title *</label>
              <input v-model="requestForm.title" type="text" class="input w-full" placeholder="Brief description of issue" required>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-gray-600">Equipment Type</label>
                <select v-model="requestForm.equipment_type" class="input w-full">
                  <option value="REACTOR">Reactor</option>
                  <option value="TANK">Storage Tank</option>
                  <option value="PUMP">Pump</option>
                  <option value="CONVEYOR">Conveyor</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <div>
                <label class="block text-sm text-gray-600">Equipment Name</label>
                <input v-model="requestForm.equipment_name" type="text" class="input w-full" placeholder="e.g. R1, Tank-A">
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-gray-600">Request Type</label>
                <select v-model="requestForm.request_type" class="input w-full">
                  <option value="BREAKDOWN">Breakdown</option>
                  <option value="PREVENTIVE">Preventive</option>
                  <option value="CORRECTIVE">Corrective</option>
                  <option value="INSPECTION">Inspection</option>
                </select>
              </div>
              <div>
                <label class="block text-sm text-gray-600">Priority</label>
                <select v-model="requestForm.priority" class="input w-full">
                  <option value="LOW">Low</option>
                  <option value="MEDIUM">Medium</option>
                  <option value="HIGH">High</option>
                  <option value="CRITICAL">Critical</option>
                </select>
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600">Description</label>
              <textarea v-model="requestForm.description" rows="3" class="input w-full" placeholder="Detailed description of the issue..."></textarea>
            </div>
            <div>
              <label class="block text-sm text-gray-600">Requested By</label>
              <input v-model="requestForm.requested_by" type="text" class="input w-full" placeholder="Your name">
            </div>
            <div class="flex justify-end space-x-3 pt-2">
              <button type="button" @click="showRequestModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Creating...' : 'Create Request' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Complete Request Modal -->
    <div v-if="showCompleteRequestModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showCompleteRequestModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Complete Request - {{ selectedRequest?.request_number }}</h3>
          <form @submit.prevent="completeRequestAction" class="space-y-4">
            <div>
              <label class="block text-sm text-gray-600">Resolution Notes *</label>
              <textarea v-model="completeRequestForm.resolution_notes" rows="3" class="input w-full" required></textarea>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm text-gray-600">Downtime (hours)</label>
                <input v-model.number="completeRequestForm.downtime_hours" type="number" step="0.5" class="input w-full">
              </div>
              <div>
                <label class="block text-sm text-gray-600">Labor (hours)</label>
                <input v-model.number="completeRequestForm.labor_hours" type="number" step="0.5" class="input w-full">
              </div>
            </div>
            <div>
              <label class="block text-sm text-gray-600">Parts Cost (₹)</label>
              <input v-model.number="completeRequestForm.parts_cost" type="number" class="input w-full">
            </div>
            <div class="flex justify-end space-x-3 pt-2">
              <button type="button" @click="showCompleteRequestModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Completing...' : 'Complete' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Complete Task Modal (existing) -->
    <div v-if="showCompleteModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showCompleteModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Complete Cleaning - {{ selectedReactor?.reactor_code }}</h3>
          <form @submit.prevent="completeTask" class="space-y-4">
            <div>
              <label class="block text-sm text-gray-600">Performed By</label>
              <input type="text" v-model="completeForm.performed_by" class="input w-full" placeholder="Operator name">
            </div>
            <div>
              <label class="block text-sm text-gray-600">Notes</label>
              <textarea v-model="completeForm.notes" rows="2" class="input w-full"></textarea>
            </div>
            <div class="bg-green-50 border border-green-200 rounded p-3">
              <p class="text-sm text-green-700">✅ Counter will reset to 0</p>
            </div>
            <div class="flex justify-end space-x-3">
              <button type="button" @click="showCompleteModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">Complete</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { maintenanceApi } from '../services/api'

const activeTab = ref('reactors')
const reactorStatus = ref([])
const dueTasks = ref([])
const warningTasks = ref([])
const logs = ref([])
const requests = ref([])
const requestSummary = ref({ open: 0, in_progress: 0, on_hold: 0, completed: 0, total_active: 0 })
const requestFilter = ref('')

// Modals
const showCompleteModal = ref(false)
const showRequestModal = ref(false)
const showCompleteRequestModal = ref(false)
const selectedReactor = ref(null)
const selectedRequest = ref(null)
const saving = ref(false)

// Forms
const completeForm = ref({ task_name: 'Carbon Cleaning', performed_by: '', notes: '' })
const requestForm = ref({ title: '', equipment_type: 'REACTOR', equipment_name: '', request_type: 'BREAKDOWN', priority: 'MEDIUM', description: '', requested_by: '' })
const completeRequestForm = ref({ resolution_notes: '', downtime_hours: null, labor_hours: null, parts_cost: null })

const okReactors = computed(() => reactorStatus.value.filter(r => r.maintenance_status === 'OK').length)
const filteredRequests = computed(() => {
  if (!requestFilter.value) return requests.value
  return requests.value.filter(r => r.status === requestFilter.value)
})

const loadData = async () => {
  try {
    const [statusRes, dueRes, logsRes, reqRes, summaryRes] = await Promise.all([
      maintenanceApi.getReactorStatus(),
      maintenanceApi.getDueTasks(),
      maintenanceApi.listLogs(null, 20),
      maintenanceApi.listRequests(),
      maintenanceApi.getRequestsSummary()
    ])
    reactorStatus.value = statusRes.data
    dueTasks.value = dueRes.data.due || []
    warningTasks.value = dueRes.data.warning || []
    logs.value = logsRes.data
    requests.value = reqRes.data
    requestSummary.value = summaryRes.data
  } catch (e) { console.error(e) }
}

const getCardClass = (r) => {
  if (r.maintenance_status === 'BREAKDOWN') return 'border-2 border-red-500 bg-red-100'
  if (r.maintenance_status === 'BLOCKED') return 'border-2 border-red-400 bg-red-50'
  if (r.maintenance_status === 'WARNING') return 'border-2 border-yellow-400 bg-yellow-50'
  return 'border border-gray-200'
}
const getStatusBadge = (s) => {
  if (s === 'BREAKDOWN') return 'bg-red-600 text-white'
  if (s === 'BLOCKED') return 'bg-red-100 text-red-700'
  if (s === 'WARNING') return 'bg-yellow-100 text-yellow-700'
  return 'bg-green-100 text-green-700'
}
const getProgressWidth = (r) => Math.min((r.batches_since_cleaning / r.maintenance_frequency) * 100, 100) + '%'
const getProgressColor = (r) => r.maintenance_status === 'BLOCKED' ? 'bg-red-500' : r.maintenance_status === 'WARNING' ? 'bg-yellow-500' : 'bg-green-500'
const getReactorCode = (id) => reactorStatus.value.find(r => r.reactor_id === id)?.reactor_code || `R${id}`
const formatDate = (dt) => dt ? new Date(dt).toLocaleDateString() : '-'

const getTypeBadge = (t) => ({ BREAKDOWN: 'px-2 py-0.5 text-xs rounded bg-red-100 text-red-700', PREVENTIVE: 'px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-700', CORRECTIVE: 'px-2 py-0.5 text-xs rounded bg-yellow-100 text-yellow-700', INSPECTION: 'px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-700' }[t] || '')
const getPriorityBadge = (p) => ({ CRITICAL: 'px-2 py-0.5 text-xs rounded bg-red-600 text-white', HIGH: 'px-2 py-0.5 text-xs rounded bg-orange-100 text-orange-700', MEDIUM: 'px-2 py-0.5 text-xs rounded bg-yellow-100 text-yellow-700', LOW: 'px-2 py-0.5 text-xs rounded bg-gray-100 text-gray-600' }[p] || '')
const getReqStatusBadge = (s) => ({ OPEN: 'px-2 py-0.5 text-xs rounded bg-yellow-100 text-yellow-700', IN_PROGRESS: 'px-2 py-0.5 text-xs rounded bg-blue-100 text-blue-700', ON_HOLD: 'px-2 py-0.5 text-xs rounded bg-orange-100 text-orange-700', COMPLETED: 'px-2 py-0.5 text-xs rounded bg-green-100 text-green-700' }[s] || '')

const openCompleteModal = (r) => { selectedReactor.value = r; completeForm.value = { task_name: 'Carbon Cleaning', performed_by: '', notes: '' }; showCompleteModal.value = true }

const completeTask = async () => {
  saving.value = true
  try {
    const formData = new FormData()
    formData.append('reactor_id', selectedReactor.value.reactor_id)
    formData.append('task_name', completeForm.value.task_name)
    formData.append('performed_by', completeForm.value.performed_by || 'Operator')
    if (completeForm.value.notes) formData.append('notes', completeForm.value.notes)
    await maintenanceApi.completeTask(formData)
    showCompleteModal.value = false
    loadData()
  } catch (e) { alert('Error: ' + (e.response?.data?.detail || e.message)) }
  finally { saving.value = false }
}

const createRequest = async () => {
  if (!requestForm.value.title) return
  saving.value = true
  try {
    await maintenanceApi.createRequest(requestForm.value)
    showRequestModal.value = false
    requestForm.value = { title: '', equipment_type: 'REACTOR', equipment_name: '', request_type: 'BREAKDOWN', priority: 'MEDIUM', description: '', requested_by: '' }
    loadData()
  } catch (e) { alert('Error: ' + (e.response?.data?.detail || e.message)) }
  finally { saving.value = false }
}

const markInProgress = async (req) => {
  try {
    await maintenanceApi.updateRequestStatus(req.id, 'IN_PROGRESS')
    loadData()
  } catch (e) { alert('Error: ' + e.message) }
}

const openCompleteRequestModal = (req) => { selectedRequest.value = req; completeRequestForm.value = { resolution_notes: '', downtime_hours: null, labor_hours: null, parts_cost: null }; showCompleteRequestModal.value = true }

const completeRequestAction = async () => {
  saving.value = true
  try {
    await maintenanceApi.completeRequest(selectedRequest.value.id, { resolution_notes: completeRequestForm.value.resolution_notes, resolved_by: 'Technician', downtime_hours: completeRequestForm.value.downtime_hours, labor_hours: completeRequestForm.value.labor_hours, parts_cost: completeRequestForm.value.parts_cost })
    showCompleteRequestModal.value = false
    loadData()
  } catch (e) { alert('Error: ' + (e.response?.data?.detail || e.message)) }
  finally { saving.value = false }
}

onMounted(loadData)
</script>
