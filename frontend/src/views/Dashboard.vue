<template>
  <div class="space-y-6">
    <!-- Header -->
    <div class="flex justify-between items-center">
      <div>
        <h1 class="text-2xl font-bold text-gray-900">Operations Dashboard</h1>
        <p class="text-sm text-gray-500">Real-time plant status • {{ currentTime }}</p>
      </div>
      <button @click="loadAll" class="btn btn-secondary text-sm">
        🔄 Refresh
      </button>
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex items-center justify-center py-20">
      <div class="animate-spin rounded-full h-10 w-10 border-b-2 border-blue-600"></div>
    </div>

    <div v-else>
      <!-- ═══════════════════════════════════════════════════════════════ -->
      <!-- ROW 1: KPI CARDS IN 3 FLOW ZONES -->
      <!-- ═══════════════════════════════════════════════════════════════ -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
        <!-- INPUT ZONE -->
        <div class="bg-gradient-to-br from-green-50 to-green-100 rounded-xl p-4 border border-green-200">
          <h3 class="text-xs font-semibold text-green-700 uppercase mb-3 flex items-center">
            <span class="mr-2">📥</span> Input (Procurement)
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">Vendors</p>
              <p class="text-xl font-bold text-green-700">{{ summary.input?.active_vendors || 0 }}</p>
            </div>
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">Open POs</p>
              <p class="text-xl font-bold text-green-700">{{ summary.input?.open_purchase_orders || 0 }}</p>
            </div>
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">Today's GRNs</p>
              <p class="text-xl font-bold text-green-700">{{ summary.input?.todays_grns || 0 }}</p>
            </div>
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">Material In</p>
              <p class="text-xl font-bold text-green-700">{{ formatNumber(summary.input?.todays_material_kg) }} kg</p>
            </div>
          </div>
        </div>

        <!-- PROCESS ZONE -->
        <div class="bg-gradient-to-br from-purple-50 to-purple-100 rounded-xl p-4 border border-purple-200">
          <h3 class="text-xs font-semibold text-purple-700 uppercase mb-3 flex items-center">
            <span class="mr-2">⚙️</span> Process (Production)
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">Active Batches</p>
              <p class="text-xl font-bold text-purple-700">{{ summary.process?.active_batches || 0 }}</p>
            </div>
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">Oil in Tanks</p>
              <p class="text-xl font-bold text-purple-700">{{ formatNumber(summary.process?.oil_in_tanks_liters) }} L</p>
            </div>
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">Tank Fill</p>
              <p class="text-xl font-bold" :class="summary.process?.tank_fill_percent > 90 ? 'text-red-600' : 'text-purple-700'">
                {{ summary.process?.tank_fill_percent || 0 }}%
              </p>
            </div>
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">Raw Stock</p>
              <p class="text-xl font-bold" :class="summary.process?.raw_material_stock_kg < 500 ? 'text-red-600' : 'text-purple-700'">
                {{ formatNumber(summary.process?.raw_material_stock_kg) }} kg
              </p>
            </div>
          </div>
        </div>

        <!-- OUTPUT ZONE -->
        <div class="bg-gradient-to-br from-blue-50 to-blue-100 rounded-xl p-4 border border-blue-200">
          <h3 class="text-xs font-semibold text-blue-700 uppercase mb-3 flex items-center">
            <span class="mr-2">📤</span> Output (Sales)
          </h3>
          <div class="grid grid-cols-2 gap-3">
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">Customers</p>
              <p class="text-xl font-bold text-blue-700">{{ summary.output?.active_customers || 0 }}</p>
            </div>
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">Pending Dispatch</p>
              <p class="text-xl font-bold text-blue-700">{{ summary.output?.pending_dispatches || 0 }}</p>
            </div>
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">YTD Revenue</p>
              <p class="text-xl font-bold text-blue-700">₹{{ formatLakhs(summary.output?.ytd_revenue) }}</p>
            </div>
            <div class="bg-white rounded-lg p-3 shadow-sm">
              <p class="text-xs text-gray-500">30-Day Revenue</p>
              <p class="text-xl font-bold text-blue-700">₹{{ formatLakhs(summary.output?.trailing_30d_revenue) }}</p>
            </div>
          </div>
          <!-- Margin badge -->
          <div class="mt-3 flex justify-between items-center bg-white rounded-lg p-2 shadow-sm">
            <span class="text-xs text-gray-500">YTD Margin</span>
            <span class="text-lg font-bold" :class="summary.output?.profit_margin_pct >= 30 ? 'text-green-600' : 'text-blue-700'">
              {{ summary.output?.profit_margin_pct || 0 }}%
            </span>
          </div>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════ -->
      <!-- ROW 2: REACTOR STATUS + ALERTS -->
      <!-- ═══════════════════════════════════════════════════════════════ -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- REACTOR STATUS (2/3 width) -->
        <div class="lg:col-span-2 card">
          <div class="card-header flex justify-between items-center">
            <h2 class="text-lg font-semibold">Reactor Status</h2>
            <router-link to="/production" class="text-sm text-blue-600 hover:underline">View Production →</router-link>
          </div>
          <div class="card-body">
            <div class="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <div
                v-for="reactor in summary.process?.reactors || []"
                :key="reactor.id"
                class="relative p-4 rounded-xl border-2 transition-all"
                :class="getReactorCardClass(reactor)"
              >
                <!-- Status indicator dot -->
                <div
                  class="absolute top-3 right-3 w-3 h-3 rounded-full"
                  :class="getReactorDotClass(reactor)"
                ></div>
                
                <div class="text-center">
                  <p class="text-2xl font-bold text-gray-800">{{ reactor.code }}</p>
                  <p class="text-xs text-gray-500">{{ reactor.name }}</p>
                  <div class="mt-3 py-2 px-3 rounded-lg text-sm font-medium" :class="getReactorBadgeClass(reactor)">
                    {{ reactor.status }}
                  </div>
                  <div class="mt-2 text-xs text-gray-500">
                    Batches: {{ reactor.batches_since_clean }}/{{ reactor.max_batches }}
                  </div>
                  <!-- Progress bar -->
                  <div class="mt-2 w-full h-1.5 bg-gray-200 rounded-full">
                    <div
                      class="h-1.5 rounded-full transition-all"
                      :class="reactor.batches_since_clean >= reactor.max_batches ? 'bg-red-500' : 'bg-green-500'"
                      :style="{ width: `${(reactor.batches_since_clean / reactor.max_batches) * 100}%` }"
                    ></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- ALERTS PANEL (1/3 width) -->
        <div class="card">
          <div class="card-header">
            <h2 class="text-lg font-semibold flex items-center">
              <span class="mr-2">🔔</span> Alerts
              <span v-if="alerts.count > 0" class="ml-2 bg-red-100 text-red-700 text-xs px-2 py-0.5 rounded-full">
                {{ alerts.count }}
              </span>
            </h2>
          </div>
          <div class="card-body max-h-64 overflow-y-auto">
            <div v-if="alerts.alerts?.length === 0" class="text-center text-gray-400 py-6">
              ✅ No alerts
            </div>
            <div v-else class="space-y-2">
              <router-link
                v-for="(alert, idx) in alerts.alerts"
                :key="idx"
                :to="alert.link"
                class="block p-3 rounded-lg hover:bg-gray-50 border transition-colors"
                :class="{
                  'border-red-200 bg-red-50': alert.severity === 'critical',
                  'border-yellow-200 bg-yellow-50': alert.severity === 'warning',
                  'border-blue-200 bg-blue-50': alert.severity === 'info'
                }"
              >
                <div class="flex items-start">
                  <span class="text-lg mr-2">{{ alert.icon }}</span>
                  <p class="text-sm text-gray-700 flex-1">{{ alert.message }}</p>
                  <span class="text-gray-400 text-xs">→</span>
                </div>
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════ -->
      <!-- ROW 3: QUICK ACTIONS + ACTIVITY FEED -->
      <!-- ═══════════════════════════════════════════════════════════════ -->
      <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <!-- QUICK ACTIONS -->
        <div class="card">
          <div class="card-header">
            <h2 class="text-lg font-semibold">Quick Actions</h2>
          </div>
          <div class="card-body grid grid-cols-2 gap-3">
            <router-link to="/inward-entry" class="btn bg-green-100 text-green-700 hover:bg-green-200 justify-center">
              📥 New GRN
            </router-link>
            <router-link to="/production" class="btn bg-purple-100 text-purple-700 hover:bg-purple-200 justify-center">
              🔥 Start Batch
            </router-link>
            <router-link to="/purchase-orders" class="btn bg-yellow-100 text-yellow-700 hover:bg-yellow-200 justify-center">
              📝 New PO
            </router-link>
            <router-link to="/sales" class="btn bg-blue-100 text-blue-700 hover:bg-blue-200 justify-center">
              🛒 New Sale
            </router-link>
            <router-link to="/sales?tab=dispatches" class="btn bg-cyan-100 text-cyan-700 hover:bg-cyan-200 justify-center">
              🚚 Dispatch
            </router-link>
            <router-link to="/maintenance" class="btn bg-orange-100 text-orange-700 hover:bg-orange-200 justify-center">
              🔧 Maintenance
            </router-link>
          </div>
        </div>

        <!-- ACTIVITY FEED (2/3 width) -->
        <div class="lg:col-span-2 card">
          <div class="card-header flex justify-between items-center">
            <h2 class="text-lg font-semibold flex items-center">
              <span class="mr-2">📜</span> Recent Activity
            </h2>
            <span class="text-xs text-gray-400">Auto-refreshes every 30s</span>
          </div>
          <div class="card-body max-h-72 overflow-y-auto">
            <div v-if="activity.activities?.length === 0" class="text-center text-gray-400 py-6">
              No recent activity
            </div>
            <div v-else class="space-y-2">
              <router-link
                v-for="(item, idx) in activity.activities"
                :key="idx"
                :to="item.link"
                class="flex items-center p-2 rounded hover:bg-gray-50 border-b border-gray-100 transition-colors"
              >
                <span class="text-lg mr-3">{{ item.icon }}</span>
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-gray-700 truncate">{{ item.message }}</p>
                </div>
                <span class="text-xs text-gray-400 ml-2 whitespace-nowrap">{{ formatTimestamp(item.timestamp) }}</span>
              </router-link>
            </div>
          </div>
        </div>
      </div>

      <!-- ═══════════════════════════════════════════════════════════════ -->
      <!-- ROW 4: MONTH OUTPUTS SUMMARY -->
      <!-- ═══════════════════════════════════════════════════════════════ -->
      <div class="card">
        <div class="card-header">
          <h2 class="text-lg font-semibold">This Month's Production Output</h2>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-3 gap-4 text-center">
            <div class="p-4 bg-blue-50 rounded-xl">
              <p class="text-3xl font-bold text-blue-600">{{ formatNumber(summary.process?.month_oil_liters) }}</p>
              <p class="text-sm text-gray-500">Litres Oil</p>
            </div>
            <div class="p-4 bg-gray-100 rounded-xl">
              <p class="text-3xl font-bold text-gray-700">{{ formatNumber(summary.process?.month_carbon_kg) }}</p>
              <p class="text-sm text-gray-500">kg Carbon</p>
            </div>
            <div class="p-4 bg-gray-50 rounded-xl">
              <p class="text-3xl font-bold text-gray-500">{{ formatNumber(summary.process?.month_steel_kg) }}</p>
              <p class="text-sm text-gray-500">kg Steel</p>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { dashboardApi } from '../services/api'

// State
const loading = ref(true)
const summary = ref({})
const alerts = ref({ count: 0, alerts: [] })
const activity = ref({ count: 0, activities: [] })

// Auto-refresh interval
let refreshInterval = null

// Current time
const currentTime = computed(() => {
  return new Date().toLocaleString('en-IN', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  })
})

// Formatters
const formatNumber = (num) => {
  if (num === null || num === undefined || isNaN(num)) return '0'
  return new Intl.NumberFormat('en-IN').format(Math.round(num))
}

const formatLakhs = (num) => {
  if (!num) return '0'
  if (num >= 100000) {
    return (num / 100000).toFixed(2) + 'L'
  }
  return formatNumber(num)
}

const formatTimestamp = (timestamp) => {
  if (!timestamp) return ''
  const date = new Date(timestamp)
  const now = new Date()
  const diff = (now - date) / 1000 / 60 // minutes
  
  if (diff < 1) return 'Just now'
  if (diff < 60) return `${Math.round(diff)}m ago`
  if (diff < 1440) return `${Math.round(diff / 60)}h ago`
  return date.toLocaleDateString('en-IN', { day: 'numeric', month: 'short' })
}

// Reactor styling
const getReactorCardClass = (reactor) => {
  if (reactor.status === 'MAINTENANCE' || reactor.status === 'BLOCKED') {
    return 'border-red-300 bg-red-50'
  }
  if (reactor.status === 'IN_PROGRESS' || reactor.status === 'RUNNING') {
    return 'border-green-300 bg-green-50'
  }
  if (reactor.status === 'WARNING') {
    return 'border-yellow-300 bg-yellow-50'
  }
  return 'border-gray-200 bg-gray-50'
}

const getReactorDotClass = (reactor) => {
  if (reactor.status === 'IN_PROGRESS' || reactor.status === 'RUNNING' || reactor.status === 'HEATING') {
    return 'bg-green-500 animate-pulse'
  }
  if (reactor.status === 'MAINTENANCE' || reactor.status === 'BLOCKED') {
    return 'bg-red-500'
  }
  if (reactor.status === 'WARNING') {
    return 'bg-yellow-500 animate-pulse'
  }
  return 'bg-gray-400'
}

const getReactorBadgeClass = (reactor) => {
  if (reactor.status === 'IN_PROGRESS' || reactor.status === 'RUNNING' || reactor.status === 'HEATING') {
    return 'bg-green-100 text-green-700'
  }
  if (reactor.status === 'MAINTENANCE' || reactor.status === 'BLOCKED') {
    return 'bg-red-100 text-red-700'
  }
  if (reactor.status === 'WARNING') {
    return 'bg-yellow-100 text-yellow-700'
  }
  if (reactor.status === 'COOLING') {
    return 'bg-blue-100 text-blue-700'
  }
  return 'bg-gray-100 text-gray-600'
}

// Load data
const loadAll = async () => {
  loading.value = true
  try {
    const [summaryRes, alertsRes, activityRes] = await Promise.all([
      dashboardApi.getSummary(),
      dashboardApi.getAlerts(),
      dashboardApi.getActivity(15)
    ])
    
    summary.value = summaryRes.data
    alerts.value = alertsRes.data
    activity.value = activityRes.data
  } catch (e) {
    console.error('Dashboard load error:', e)
  } finally {
    loading.value = false
  }
}

// Lifecycle
onMounted(() => {
  loadAll()
  // Auto-refresh every 30 seconds
  refreshInterval = setInterval(loadAll, 30000)
})

onUnmounted(() => {
  if (refreshInterval) {
    clearInterval(refreshInterval)
  }
})
</script>

<style scoped>
/* Reactor pulse animation for active state */
@keyframes pulse-green {
  0%, 100% { box-shadow: 0 0 0 0 rgba(34, 197, 94, 0.4); }
  50% { box-shadow: 0 0 0 8px rgba(34, 197, 94, 0); }
}

.animate-pulse-green {
  animation: pulse-green 2s infinite;
}
</style>
