<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Production Control Room</h2>
        <p class="text-sm text-gray-500">Monitor reactors, batches, and tank levels</p>
      </div>
      <button @click="showNewBatchModal = true" class="btn btn-primary btn-lg">
        <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Start New Batch
      </button>
    </div>

    <!-- Output Summary Widget -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <div class="card p-4 text-center bg-gradient-to-br from-green-50 to-green-100">
        <p class="text-3xl font-bold text-green-600">{{ summary.active_batches || 0 }}</p>
        <p class="text-sm text-gray-600">Active Batches</p>
      </div>
      <div class="card p-4 text-center bg-gradient-to-br from-yellow-50 to-yellow-100">
        <p class="text-3xl font-bold text-yellow-600">{{ summary.oil_in_tanks_liters?.toLocaleString() || 0 }}</p>
        <p class="text-sm text-gray-600">Oil in Tanks (L)</p>
      </div>
      <div class="card p-4 text-center bg-gradient-to-br from-gray-50 to-gray-100">
        <p class="text-3xl font-bold text-gray-700">{{ summary.carbon_stock_kg?.toLocaleString() || 0 }}</p>
        <p class="text-sm text-gray-600">Carbon Stock (kg)</p>
      </div>
      <div class="card p-4 text-center bg-gradient-to-br from-blue-50 to-blue-100">
        <p class="text-3xl font-bold text-blue-600">{{ summary.steel_stock_kg?.toLocaleString() || 0 }}</p>
        <p class="text-sm text-gray-600">Steel Stock (kg)</p>
      </div>
    </div>

    <!-- Main Grid: Reactors + Tanks -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
      
      <!-- Reactors Section (2 cols) -->
      <div class="lg:col-span-2">
        <div class="card">
          <div class="card-header bg-gray-50 flex justify-between items-center">
            <h3 class="text-sm font-medium text-gray-900">Reactors</h3>
            <button @click="showAddReactorModal = true" class="text-sm text-green-600 hover:text-green-800">+ Add Reactor</button>
          </div>
          <div class="card-body">
            <div v-if="reactors.length === 0" class="text-center py-8 text-gray-500">
              No reactors configured. Add your first reactor.
            </div>
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              <div 
                v-for="reactor in reactors" 
                :key="reactor.id"
                class="p-4 rounded-lg border-2 transition-all"
                :class="getReactorCardClass(reactor.status)"
              >
                <!-- Reactor Header -->
                <div class="flex justify-between items-start mb-3">
                  <div>
                    <h4 class="text-lg font-bold text-gray-900">{{ reactor.reactor_code }}</h4>
                    <p class="text-xs text-gray-500">{{ reactor.name }}</p>
                  </div>
                  <span 
                    class="px-2 py-1 rounded-full text-xs font-bold"
                    :class="getStatusBadgeClass(reactor.status)"
                  >
                    {{ reactor.status }}
                  </span>
                </div>
                
                <!-- Status Icon -->
                <div class="flex justify-center my-4">
                  <div 
                    class="w-16 h-16 rounded-full flex items-center justify-center"
                    :class="getStatusIconBg(reactor.status)"
                  >
                    <span class="text-2xl">{{ getStatusIcon(reactor.status) }}</span>
                  </div>
                </div>
                
                <!-- Stage Info (if batch running) -->
                <div v-if="getReactorBatch(reactor.id)" class="text-center mb-3">
                  <p class="text-xs font-semibold text-gray-700 uppercase tracking-wide">Current Stage</p>
                  <p class="text-lg font-bold" :class="getStageColor(getReactorBatch(reactor.id)?.current_stage)">{{ getReactorBatch(reactor.id)?.current_stage || '-' }}</p>
                  
                  <!-- Stage Controls -->
                  <div class="mt-3 space-y-2">
                    <button 
                      @click="advanceStage(getReactorBatch(reactor.id))"
                      class="w-full px-3 py-2 text-xs font-medium text-white bg-green-600 rounded-lg hover:bg-green-700 transition-colors"
                    >
                      ✓ Complete Stage → Next
                    </button>
                  </div>
                </div>
                
                <!-- Info -->
                <div class="text-center text-sm text-gray-600">
                  <p>Capacity: <span class="font-medium">{{ reactor.capacity_kg?.toLocaleString() }} kg</span></p>
                  <p>Batches: <span class="font-medium">{{ reactor.total_batches_processed }}</span></p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- Tank Farm Section (1 col) -->
      <div>
        <div class="card h-full">
          <div class="card-header bg-blue-50 flex justify-between items-center">
            <h3 class="text-sm font-medium text-blue-900">Tank Farm</h3>
            <button @click="showAddTankModal = true" class="text-sm text-blue-600 hover:text-blue-800">+ Add Tank</button>
          </div>
          <div class="card-body">
            <div v-if="tanks.length === 0" class="text-center py-8 text-gray-500">
              No tanks configured.
            </div>
            <div class="space-y-4">
              <div v-for="tank in tanks" :key="tank.id" class="p-3 bg-gray-50 rounded-lg">
                <div class="flex justify-between items-center mb-2">
                  <span class="font-medium text-gray-900">{{ tank.tank_code }}</span>
                  <span class="text-xs text-gray-500">{{ tank.material_type }}</span>
                </div>
                
                <!-- Tank Gauge -->
                <div class="relative h-8 bg-gray-200 rounded-full overflow-hidden">
                  <div 
                    class="absolute inset-y-0 left-0 rounded-full transition-all duration-500"
                    :class="getTankFillColor(tank.fill_percentage)"
                    :style="{ width: Math.min(tank.fill_percentage, 100) + '%' }"
                  ></div>
                  <div class="absolute inset-0 flex items-center justify-center text-xs font-bold text-gray-700">
                    {{ tank.fill_percentage.toFixed(1) }}%
                  </div>
                </div>
                
                <div class="flex justify-between mt-2 text-xs text-gray-500">
                  <span>{{ tank.current_level_liters?.toLocaleString() }} L</span>
                  <span>/ {{ tank.capacity_liters?.toLocaleString() }} L</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Recent Batches -->
    <div class="card">
      <div class="card-header bg-gray-50">
        <h3 class="text-sm font-medium text-gray-900">Recent Batches</h3>
      </div>
      <div class="overflow-x-auto">
        <table class="min-w-full divide-y divide-gray-200 table-dense">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Batch</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reactor</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Input (kg)</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Oil (kg)</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Carbon</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Steel</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Loss</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Stage</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
              <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
            </tr>
          </thead>
          <tbody class="bg-white divide-y divide-gray-200">
            <tr v-for="batch in batches" :key="batch.id" class="hover:bg-gray-50">
              <td class="px-4 py-3 font-medium text-gray-900">{{ batch.batch_number }}</td>
              <td class="px-4 py-3 text-gray-600">{{ getReactorCode(batch.reactor_id) }}</td>
              <td class="px-4 py-3 text-gray-900">{{ batch.input_weight_kg?.toLocaleString() }}</td>
              <td class="px-4 py-3 text-green-600 font-medium">{{ batch.oil_output_kg?.toLocaleString() || '-' }}</td>
              <td class="px-4 py-3 text-gray-900">{{ batch.carbon_output_kg?.toLocaleString() || '-' }}</td>
              <td class="px-4 py-3 text-gray-900">{{ batch.steel_output_kg?.toLocaleString() || '-' }}</td>
              <td class="px-4 py-3 text-red-500">{{ batch.syn_gas_loss_kg?.toLocaleString() || '-' }}</td>
              <td class="px-4 py-3">
                <span v-if="batch.status === 'COMPLETED'" class="font-semibold text-green-600">✓ Completed</span>
                <span v-else-if="batch.current_stage" class="font-semibold" :class="getStageColor(batch.current_stage)">{{ batch.current_stage }}</span>
                <span v-else class="text-gray-400">-</span>
              </td>
              <td class="px-4 py-3">
                <span :class="getBatchStatusBadge(batch.status)" class="badge">{{ batch.status }}</span>
              </td>
              <td class="px-4 py-3">
                <button 
                  v-if="batch.status !== 'COMPLETED' && batch.status !== 'CANCELLED'"
                  @click="openCompleteModal(batch)"
                  class="text-green-600 hover:text-green-800 text-sm font-medium"
                >
                  🏁 Complete All
                </button>
              </td>
            </tr>
            <tr v-if="batches.length === 0">
              <td colspan="10" class="px-4 py-8 text-center text-gray-500">No batches yet</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- New Batch Modal -->
    <div v-if="showNewBatchModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showNewBatchModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-lg w-full">
          <div class="px-6 py-4 border-b">
            <h3 class="text-lg font-medium text-gray-900">Start New Batch</h3>
          </div>
          <form @submit.prevent="startBatch" class="px-6 py-4 space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Select Reactor *</label>
              <select v-model="newBatch.reactor_id" required class="mt-1 input">
                <option value="">-- Select Reactor --</option>
                <option v-for="r in availableReactors" :key="r.id" :value="r.id">
                  {{ r.reactor_code }} - {{ r.name }} ({{ r.capacity_kg }}kg)
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Recipe (for stage tracking)</label>
              <select v-model="newBatch.recipe_id" class="mt-1 input">
                <option value="">-- No Recipe (Manual) --</option>
                <option v-for="r in recipes" :key="r.id" :value="r.id">
                  {{ r.name }} ({{ r.stage_count }} stages, {{ r.total_duration_minutes }} min)
                </option>
              </select>
              <p v-if="newBatch.recipe_id" class="text-xs text-green-600 mt-1">✓ Expected end time will be calculated</p>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Raw Material Lot (FIFO) *</label>
              <select v-model="newBatch.input_lot_id" required class="mt-1 input">
                <option value="">-- Select Lot (Oldest First) --</option>
                <option v-for="lot in availableLots" :key="lot.id" :value="lot.id">
                  {{ lot.lot_id }} - {{ lot.current_qty_kg }}kg available @ ₹{{ lot.rate_per_kg }}/kg
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Input Weight (kg) *</label>
              <input v-model.number="newBatch.input_weight_kg" type="number" required min="1" class="mt-1 input">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Meter Start Reading (kWh) *</label>
              <input v-model.number="newBatch.meter_start" type="number" required step="0.01" class="mt-1 input">
            </div>
            <div class="flex justify-end space-x-3 pt-4 border-t">
              <button type="button" @click="showNewBatchModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ saving ? 'Starting...' : 'Start Batch' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Complete Batch Modal -->
    <div v-if="showCompleteModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showCompleteModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-2xl w-full">
          <div class="px-6 py-4 border-b bg-green-50">
            <h3 class="text-lg font-medium text-green-900">Complete Batch: {{ completingBatch?.batch_number }}</h3>
          </div>
          <form @submit.prevent="completeBatch" class="px-6 py-4 space-y-4">
            <div class="bg-gray-50 p-3 rounded">
              <p class="text-sm text-gray-600">Input: <span class="font-bold text-gray-900">{{ completingBatch?.input_weight_kg?.toLocaleString() }} kg</span></p>
            </div>
            
            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Oil Output (kg) *</label>
                <input v-model.number="completeForm.oil_output_kg" type="number" required min="0" step="0.01" class="mt-1 input" @input="calcYields">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Carbon Output (kg) *</label>
                <input v-model.number="completeForm.carbon_output_kg" type="number" required min="0" step="0.01" class="mt-1 input" @input="calcYields">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Steel Output (kg) *</label>
                <input v-model.number="completeForm.steel_output_kg" type="number" required min="0" step="0.01" class="mt-1 input" @input="calcYields">
              </div>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700">Destination Tank for Oil *</label>
              <select v-model="completeForm.destination_tank_id" required class="mt-1 input">
                <option value="">-- Select Tank --</option>
                <option v-for="t in tanks" :key="t.id" :value="t.id">
                  {{ t.tank_code }} - {{ t.name }} ({{ t.fill_percentage.toFixed(0) }}% full)
                </option>
              </select>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700">Meter End Reading (kWh) *</label>
              <input v-model.number="completeForm.meter_end" type="number" required step="0.01" class="mt-1 input">
            </div>
            
            <!-- Calculated Preview -->
            <div class="bg-green-50 p-4 rounded-lg border border-green-200">
              <h4 class="text-sm font-medium text-green-800 mb-2">Calculated Results</h4>
              <div class="grid grid-cols-4 gap-4 text-center">
                <div>
                  <p class="text-xs text-gray-600">Oil Yield</p>
                  <p class="text-xl font-bold text-green-600">{{ calcOilYield }}%</p>
                </div>
                <div>
                  <p class="text-xs text-gray-600">Carbon Yield</p>
                  <p class="text-xl font-bold text-gray-800">{{ calcCarbonYield }}%</p>
                </div>
                <div>
                  <p class="text-xs text-gray-600">Steel Yield</p>
                  <p class="text-xl font-bold text-gray-600">{{ calcSteelYield }}%</p>
                </div>
                <div>
                  <p class="text-xs text-gray-600">Syn Gas Loss</p>
                  <p class="text-xl font-bold text-red-500">{{ calcLoss }} kg</p>
                </div>
              </div>
            </div>
            
            <div class="flex justify-end space-x-3 pt-4 border-t">
              <button type="button" @click="showCompleteModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving || !isValidCompletion">
                {{ saving ? 'Completing...' : 'Complete Batch' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Add Reactor Modal -->
    <div v-if="showAddReactorModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showAddReactorModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Add Reactor</h3>
          <form @submit.prevent="addReactor" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Reactor Code *</label>
              <input v-model="newReactor.code" type="text" required class="mt-1 input" placeholder="R1, R2, etc.">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Name *</label>
              <input v-model="newReactor.name" type="text" required class="mt-1 input" placeholder="Reactor 1">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Capacity (kg) *</label>
              <input v-model.number="newReactor.capacity" type="number" required min="100" class="mt-1 input">
            </div>
            <div class="flex justify-end space-x-3">
              <button type="button" @click="showAddReactorModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary">Add Reactor</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Add Tank Modal -->
    <div v-if="showAddTankModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showAddTankModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Add Storage Tank</h3>
          <form @submit.prevent="addTank" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Tank Code *</label>
              <input v-model="newTank.tank_code" type="text" required class="mt-1 input" placeholder="T1, SETTLING-1">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Name *</label>
              <input v-model="newTank.name" type="text" required class="mt-1 input" placeholder="Main Oil Tank">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Type</label>
              <select v-model="newTank.tank_type" class="mt-1 input">
                <option value="SETTLING">Settling</option>
                <option value="STORAGE">Storage</option>
                <option value="SALES">Sales</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Capacity (Liters) *</label>
              <input v-model.number="newTank.capacity_liters" type="number" required min="100" class="mt-1 input">
            </div>
            <div class="flex justify-end space-x-3">
              <button type="button" @click="showAddTankModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary">Add Tank</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { productionApi, tankFarmApi } from '../../services/api'
import { useProductionAlerts } from '../../composables/useProductionAlerts'

// Start production alerts polling (15-min batch alerts, tank level alerts)
const { isPolling, activeBatches: alertBatches } = useProductionAlerts({
  pollIntervalMs: 60000,  // Poll every minute
  nearlyDoneThresholdMins: 15
})

const reactors = ref([])
const tanks = ref([])
const batches = ref([])
const availableLots = ref([])
const recipes = ref([])
const summary = ref({ active_batches: 0, oil_in_tanks_liters: 0, carbon_stock_kg: 0, steel_stock_kg: 0 })
const loading = ref(false)
const saving = ref(false)

// Modals
const showNewBatchModal = ref(false)
const showCompleteModal = ref(false)
const showAddReactorModal = ref(false)
const showAddTankModal = ref(false)

const completingBatch = ref(null)

// Forms
const newBatch = ref({ reactor_id: '', recipe_id: '', input_lot_id: '', input_weight_kg: 5000, meter_start: 0 })
const completeForm = ref({ oil_output_kg: 0, carbon_output_kg: 0, steel_output_kg: 0, destination_tank_id: '', meter_end: 0 })
const newReactor = ref({ code: '', name: '', capacity: 5000 })
const newTank = ref({ tank_code: '', name: '', tank_type: 'STORAGE', capacity_liters: 10000 })

const availableReactors = computed(() => reactors.value.filter(r => r.is_available))

// Calculations
const calcOilYield = computed(() => {
  if (!completingBatch.value) return 0
  return ((completeForm.value.oil_output_kg / completingBatch.value.input_weight_kg) * 100).toFixed(1)
})
const calcCarbonYield = computed(() => {
  if (!completingBatch.value) return 0
  return ((completeForm.value.carbon_output_kg / completingBatch.value.input_weight_kg) * 100).toFixed(1)
})
const calcSteelYield = computed(() => {
  if (!completingBatch.value) return 0
  return ((completeForm.value.steel_output_kg / completingBatch.value.input_weight_kg) * 100).toFixed(1)
})
const calcLoss = computed(() => {
  if (!completingBatch.value) return 0
  const input = completingBatch.value.input_weight_kg
  const total = completeForm.value.oil_output_kg + completeForm.value.carbon_output_kg + completeForm.value.steel_output_kg
  return (input - total).toFixed(1)
})
const isValidCompletion = computed(() => {
  if (!completingBatch.value) return false
  const total = completeForm.value.oil_output_kg + completeForm.value.carbon_output_kg + completeForm.value.steel_output_kg
  return total <= completingBatch.value.input_weight_kg && completeForm.value.destination_tank_id
})

// Load data
const loadData = async () => {
  loading.value = true
  try {
    const [reactorsRes, tanksRes, batchesRes, lotsRes, recipesRes, summaryRes] = await Promise.all([
      productionApi.listReactors(),
      tankFarmApi.listTanks(),
      productionApi.listBatches(),
      productionApi.listAvailableLots(),
      productionApi.listRecipes(),
      productionApi.getSummary()
    ])
    reactors.value = reactorsRes.data
    tanks.value = tanksRes.data
    batches.value = batchesRes.data
    availableLots.value = lotsRes.data
    recipes.value = recipesRes.data
    summary.value = summaryRes.data
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
}

// Get batch for a reactor (to show stage)
const getReactorBatch = (reactorId) => {
  return batches.value.find(b => b.reactor_id === reactorId && b.status !== 'COMPLETED' && b.status !== 'CANCELLED')
}

// Stage color helper
const getStageColor = (stage) => {
  const map = {
    'Loading': 'text-blue-600',
    'Heating': 'text-red-600',
    'Distillation': 'text-orange-600',
    'Cooling': 'text-cyan-600',
    'Unloading': 'text-yellow-600',
    'Completed': 'text-green-600'
  }
  return map[stage] || 'text-gray-800'
}

// Helpers
const getReactorCode = (id) => reactors.value.find(r => r.id === id)?.reactor_code || 'Unknown'

const getReactorCardClass = (status) => {
  const map = {
    'IDLE': 'border-green-300 bg-green-50',
    'LOADING': 'border-blue-300 bg-blue-50',
    'HEATING': 'border-red-300 bg-red-50',
    'DISTILLATION': 'border-orange-300 bg-orange-50',
    'COOLING': 'border-cyan-300 bg-cyan-50',
    'UNLOADING': 'border-yellow-300 bg-yellow-50',
    'MAINTENANCE': 'border-gray-300 bg-gray-100'
  }
  return map[status] || 'border-gray-300'
}

const getStatusBadgeClass = (status) => {
  const map = {
    'IDLE': 'bg-green-100 text-green-800',
    'LOADING': 'bg-blue-100 text-blue-800',
    'HEATING': 'bg-red-100 text-red-800',
    'DISTILLATION': 'bg-orange-100 text-orange-800',
    'COOLING': 'bg-cyan-100 text-cyan-800',
    'UNLOADING': 'bg-yellow-100 text-yellow-800',
    'MAINTENANCE': 'bg-gray-100 text-gray-800'
  }
  return map[status] || 'bg-gray-100 text-gray-800'
}

const getStatusIconBg = (status) => {
  const map = {
    'IDLE': 'bg-green-200',
    'LOADING': 'bg-blue-200',
    'HEATING': 'bg-red-200',
    'DISTILLATION': 'bg-orange-200',
    'COOLING': 'bg-cyan-200'
  }
  return map[status] || 'bg-gray-200'
}

const getStatusIcon = (status) => {
  const map = {
    'IDLE': '✓',
    'LOADING': '⏳',
    'HEATING': '🔥',
    'DISTILLATION': '💨',
    'COOLING': '❄️',
    'UNLOADING': '📤',
    'MAINTENANCE': '🔧'
  }
  return map[status] || '?'
}

const getTankFillColor = (pct) => {
  if (pct >= 90) return 'bg-red-500'
  if (pct >= 70) return 'bg-yellow-500'
  return 'bg-blue-500'
}

const getBatchStatusBadge = (status) => {
  const map = {
    'LOADING': 'badge-info',
    'IN_PROGRESS': 'badge-warning',
    'COOLING': 'badge-info',
    'COMPLETED': 'badge-success',
    'CANCELLED': 'badge-danger'
  }
  return map[status] || 'badge-info'
}

// Actions
const startBatch = async () => {
  saving.value = true
  try {
    await productionApi.startBatch(newBatch.value)
    showNewBatchModal.value = false
    newBatch.value = { reactor_id: '', input_lot_id: '', input_weight_kg: 5000, meter_start: 0 }
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const openCompleteModal = (batch) => {
  completingBatch.value = batch
  completeForm.value = { oil_output_kg: 0, carbon_output_kg: 0, steel_output_kg: 0, destination_tank_id: '', meter_end: 0 }
  showCompleteModal.value = true
}

const completeBatch = async () => {
  saving.value = true
  try {
    await productionApi.completeBatch(completingBatch.value.id, completeForm.value)
    showCompleteModal.value = false
    completingBatch.value = null
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const addReactor = async () => {
  try {
    await productionApi.createReactor(newReactor.value.code, newReactor.value.name, newReactor.value.capacity)
    showAddReactorModal.value = false
    newReactor.value = { code: '', name: '', capacity: 5000 }
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const addTank = async () => {
  try {
    await tankFarmApi.createTank(newTank.value)
    showAddTankModal.value = false
    newTank.value = { tank_code: '', name: '', tank_type: 'STORAGE', capacity_liters: 10000 }
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const advanceStage = async (batch) => {
  if (!batch) return
  
  try {
    const result = await productionApi.advanceStage(batch.id)
    alert(`✓ Stage completed! Moved to: ${result.data.current_stage}`)
    loadData()
  } catch (e) {
    const msg = e.response?.data?.detail || e.message
    // Check if it's a safety interlock
    if (msg.includes('SAFETY')) {
      alert(`⚠️ ${msg}`)
    } else {
      alert('Error: ' + msg)
    }
  }
}

const calcYields = () => {} // Triggers computed refresh

onMounted(loadData)
</script>
