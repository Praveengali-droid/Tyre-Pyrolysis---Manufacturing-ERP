<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Sales & Dispatch Overview</h2>
        <p class="text-sm text-gray-500">Click any card or row to navigate to details</p>
      </div>
    </div>

    <!-- Master Cards Row -->
    <div class="grid grid-cols-4 gap-4 mb-6">
      <!-- Customers Card -->
      <router-link to="/sales/customers" class="card p-4 text-center bg-gradient-to-br from-blue-50 to-blue-100 hover:shadow-lg transition cursor-pointer">
        <p class="text-3xl font-bold text-blue-600">{{ summary.customer_count || 0 }}</p>
        <p class="text-sm text-gray-600">Customers</p>
        <p class="text-xs text-blue-500 mt-1">View All →</p>
      </router-link>

      <!-- Products Card -->
      <router-link to="/sales/products" class="card p-4 text-center bg-gradient-to-br from-purple-50 to-purple-100 hover:shadow-lg transition cursor-pointer">
        <p class="text-3xl font-bold text-purple-600">{{ summary.product_count || 0 }}</p>
        <p class="text-sm text-gray-600">Products</p>
        <p class="text-xs text-purple-500 mt-1">View All →</p>
      </router-link>

      <!-- Total Orders -->
      <router-link to="/sales/dispatches" class="card p-4 text-center bg-gradient-to-br from-gray-50 to-gray-100 hover:shadow-lg transition cursor-pointer">
        <p class="text-3xl font-bold text-gray-700">{{ summary.orders_total || 0 }}</p>
        <p class="text-sm text-gray-600">Total Orders</p>
        <p class="text-xs text-gray-500 mt-1">All Time →</p>
      </router-link>

      <!-- Total Revenue -->
      <router-link to="/sales/dispatches" class="card p-4 text-center bg-gradient-to-br from-green-50 to-green-100 hover:shadow-lg transition cursor-pointer">
        <p class="text-2xl font-bold text-green-600">₹{{ (summary.revenue_total || 0).toLocaleString() }}</p>
        <p class="text-sm text-gray-600">Total Revenue</p>
        <p class="text-xs text-green-500 mt-1">All Time →</p>
      </router-link>
    </div>

    <!-- Time-Based Stats Grid -->
    <div class="grid grid-cols-2 gap-6 mb-6">
      
      <!-- Orders by Time Period -->
      <div class="card">
        <div class="card-header bg-gray-100">
          <h3 class="text-sm font-medium">📦 Orders by Period</h3>
        </div>
        <div class="card-body p-0">
          <div class="grid grid-cols-4 divide-x">
            <router-link to="/sales/dispatches" class="p-4 text-center hover:bg-gray-50 cursor-pointer">
              <p class="text-2xl font-bold text-gray-800">{{ summary.orders_today || 0 }}</p>
              <p class="text-xs text-gray-500">Today</p>
            </router-link>
            <router-link to="/sales/dispatches" class="p-4 text-center hover:bg-gray-50 cursor-pointer">
              <p class="text-2xl font-bold text-gray-800">{{ summary.orders_week || 0 }}</p>
              <p class="text-xs text-gray-500">This Week</p>
            </router-link>
            <router-link to="/sales/dispatches" class="p-4 text-center hover:bg-gray-50 cursor-pointer">
              <p class="text-2xl font-bold text-gray-800">{{ summary.orders_month || 0 }}</p>
              <p class="text-xs text-gray-500">This Month</p>
            </router-link>
            <router-link to="/sales/dispatches" class="p-4 text-center hover:bg-gray-50 cursor-pointer">
              <p class="text-2xl font-bold text-gray-800">{{ summary.orders_year || 0 }}</p>
              <p class="text-xs text-gray-500">This Year</p>
            </router-link>
          </div>
        </div>
      </div>

      <!-- Revenue by Time Period -->
      <div class="card">
        <div class="card-header bg-green-50">
          <h3 class="text-sm font-medium text-green-800">💰 Revenue by Period</h3>
        </div>
        <div class="card-body p-0">
          <div class="grid grid-cols-4 divide-x">
            <router-link to="/sales/dispatches" class="p-4 text-center hover:bg-green-50 cursor-pointer">
              <p class="text-lg font-bold text-green-600">₹{{ (summary.revenue_today || 0).toLocaleString() }}</p>
              <p class="text-xs text-gray-500">Today</p>
            </router-link>
            <router-link to="/sales/dispatches" class="p-4 text-center hover:bg-green-50 cursor-pointer">
              <p class="text-lg font-bold text-green-600">₹{{ (summary.revenue_week || 0).toLocaleString() }}</p>
              <p class="text-xs text-gray-500">This Week</p>
            </router-link>
            <router-link to="/sales/dispatches" class="p-4 text-center hover:bg-green-50 cursor-pointer">
              <p class="text-lg font-bold text-green-600">₹{{ (summary.revenue_month || 0).toLocaleString() }}</p>
              <p class="text-xs text-gray-500">This Month</p>
            </router-link>
            <router-link to="/sales/dispatches" class="p-4 text-center hover:bg-green-50 cursor-pointer">
              <p class="text-lg font-bold text-green-600">₹{{ (summary.revenue_year || 0).toLocaleString() }}</p>
              <p class="text-xs text-gray-500">This Year</p>
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- Bottom Grid: Top Products + Recent Dispatches -->
    <div class="grid grid-cols-3 gap-6">
      
      <!-- Top Products in Stock -->
      <div class="card">
        <div class="card-header bg-amber-50">
          <h3 class="text-sm font-medium text-amber-800">📦 Top Products (Inventory Value)</h3>
        </div>
        <div class="card-body p-0">
          <div v-if="summary.top_products?.length" class="divide-y">
            <router-link v-for="(p, i) in summary.top_products" :key="i" to="/sales/products" 
              class="flex items-center justify-between p-3 hover:bg-gray-50 cursor-pointer">
              <div class="flex items-center">
                <span class="w-6 h-6 rounded-full flex items-center justify-center text-xs font-bold mr-3"
                  :class="i === 0 ? 'bg-yellow-100 text-yellow-700' : i === 1 ? 'bg-gray-200 text-gray-600' : 'bg-orange-100 text-orange-600'">
                  {{ i + 1 }}
                </span>
                <div>
                  <p class="font-medium text-sm">{{ p.name }}</p>
                  <p class="text-xs text-gray-500">{{ p.stock }} {{ p.unit }} @ ₹{{ p.rate }}</p>
                </div>
              </div>
              <div class="text-right">
                <p class="font-bold text-green-600">₹{{ p.value.toLocaleString() }}</p>
                <span class="text-xs px-2 py-0.5 rounded" :class="getProductBadge(p.product_type)">{{ p.product_type }}</span>
              </div>
            </router-link>
          </div>
          <div v-else class="p-4 text-center text-gray-500 text-sm">
            No products with stock
          </div>
        </div>
      </div>

      <!-- Recent Dispatches (Clickable Rows) -->
      <div class="card col-span-2">
        <div class="card-header flex justify-between items-center">
          <h3 class="text-sm font-medium">🚚 Recent Dispatches</h3>
          <router-link to="/sales/dispatches" class="text-sm text-blue-600 hover:underline">View All →</router-link>
        </div>
        <div class="card-body p-0">
          <table class="w-full text-sm">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-3 py-2 text-left">Code</th>
                <th class="px-3 py-2 text-left">Type</th>
                <th class="px-3 py-2 text-left">Date</th>
                <th class="px-3 py-2 text-left">Qty</th>
                <th class="px-3 py-2 text-left">Amount</th>
                <th class="px-3 py-2 text-left">Status</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="d in recentDispatches" :key="d.type + '-' + d.id" 
                @click="goToDispatch(d)"
                class="border-t hover:bg-blue-50 cursor-pointer transition">
                <td class="px-3 py-2 font-medium text-blue-600">{{ d.dispatch_code }}</td>
                <td class="px-3 py-2">
                  <span :class="d.type === 'CARBON' ? 'px-2 py-0.5 text-xs rounded bg-gray-200' : 'px-2 py-0.5 text-xs rounded bg-yellow-100'">
                    {{ d.type }}
                  </span>
                </td>
                <td class="px-3 py-2">{{ d.dispatch_date }}</td>
                <td class="px-3 py-2">{{ d.quantity_kg }} kg</td>
                <td class="px-3 py-2 text-green-600 font-medium">₹{{ d.total_amount?.toLocaleString() }}</td>
                <td class="px-3 py-2">
                  <span v-if="d.customer_confirmed" class="text-green-600">✓ Delivered</span>
                  <span v-else class="text-orange-600">In Transit</span>
                </td>
              </tr>
              <tr v-if="recentDispatches.length === 0">
                <td colspan="6" class="px-3 py-4 text-center text-gray-500">No dispatches yet</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { salesApi } from '../../services/api'

const router = useRouter()
const summary = ref({})
const carbonDispatches = ref([])
const steelDispatches = ref([])

// Combine and sort recent dispatches
const recentDispatches = computed(() => {
  const carbon = carbonDispatches.value.map(d => ({ ...d, type: 'CARBON' }))
  const steel = steelDispatches.value.map(d => ({ ...d, type: 'STEEL' }))
  return [...carbon, ...steel]
    .sort((a, b) => new Date(b.dispatch_date) - new Date(a.dispatch_date))
    .slice(0, 8)
})

const loadData = async () => {
  try {
    const [summaryRes, carbonRes, steelRes] = await Promise.all([
      salesApi.getSummary(),
      salesApi.listCarbonDispatches(),
      salesApi.listSteelDispatches()
    ])
    summary.value = summaryRes.data
    carbonDispatches.value = carbonRes.data
    steelDispatches.value = steelRes.data
  } catch (e) {
    console.error('Failed to load data:', e)
  }
}

const goToDispatch = (dispatch) => {
  router.push(`/sales/dispatches?type=${dispatch.type}`)
}

const getProductBadge = (type) => {
  const map = {
    'OIL': 'bg-amber-100 text-amber-700',
    'CARBON': 'bg-gray-200 text-gray-700',
    'STEEL': 'bg-yellow-100 text-yellow-700',
    'OTHER': 'bg-blue-100 text-blue-700'
  }
  return map[type] || map['OTHER']
}

onMounted(loadData)
</script>
