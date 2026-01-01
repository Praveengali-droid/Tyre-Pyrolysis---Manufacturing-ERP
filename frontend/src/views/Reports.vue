<template>
  <div class="p-6">
    <!-- Header with Time Filter -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-gray-900">Reports & Analytics</h2>
        <p class="text-sm text-gray-500">Business intelligence dashboard</p>
      </div>
      <div class="flex items-center space-x-4">
        <!-- Period Selector -->
        <select v-model="period" @change="loadAllData" class="input py-2">
          <option value="7d">Last 7 Days</option>
          <option value="this_month">This Month</option>
          <option value="last_month">Last Month</option>
          <option value="ytd">Year to Date</option>
        </select>
      </div>
    </div>

    <!-- Tabs -->
    <div class="border-b border-gray-200 mb-6">
      <nav class="-mb-px flex space-x-8">
        <button 
          v-for="tab in visibleTabs" :key="tab.id"
          @click="activeTab = tab.id"
          :class="[
            activeTab === tab.id 
              ? 'border-blue-500 text-blue-600' 
              : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300',
            'whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm'
          ]"
        >
          {{ tab.name }}
        </button>
      </nav>
    </div>

    <!-- Loading State -->
    <div v-if="loading" class="flex items-center justify-center py-12">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
    </div>

    <!-- Tab Content -->
    <div v-else>
      <!-- YIELD TAB -->
      <div v-if="activeTab === 'yield'" class="space-y-6">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold">Vendor Yield Analysis</h3>
          <button @click="exportCSV('vendor')" class="btn btn-secondary text-sm">📥 Download CSV</button>
        </div>
        
        <!-- Yield Chart -->
        <div class="card p-4">
          <canvas ref="yieldChart" height="100"></canvas>
        </div>
        
        <!-- Vendor Table -->
        <div class="card">
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendor</th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Batches</th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Input (kg)</th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Oil Yield %</th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Carbon %</th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Steel %</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="v in yieldData.vendors" :key="v.vendor_id" class="hover:bg-gray-50">
                  <td class="px-4 py-3 text-sm">
                    <span :class="getRankBadge(v.rank)">{{ v.rank }}</span>
                  </td>
                  <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ v.vendor_name }}</td>
                  <td class="px-4 py-3 text-sm text-right text-gray-500">{{ v.batch_count }}</td>
                  <td class="px-4 py-3 text-sm text-right text-gray-500">{{ formatNumber(v.total_input_kg) }}</td>
                  <td class="px-4 py-3 text-sm text-right font-medium" :class="getYieldColor(v.avg_oil_yield, yieldData.target_oil_yield)">
                    {{ v.avg_oil_yield }}%
                  </td>
                  <td class="px-4 py-3 text-sm text-right text-gray-500">{{ v.avg_carbon_yield }}%</td>
                  <td class="px-4 py-3 text-sm text-right text-gray-500">{{ v.avg_steel_yield }}%</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <!-- INVENTORY TAB -->
      <div v-if="activeTab === 'inventory'" class="space-y-6">
        <h3 class="text-lg font-semibold">Inventory Valuation</h3>
        
        <!-- Summary Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="card p-6 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-200">
            <p class="text-sm text-blue-600 font-medium">Raw Materials</p>
            <p class="text-2xl font-bold text-blue-800">₹{{ formatNumber(inventoryData.raw_materials?.total_value || 0) }}</p>
          </div>
          <div class="card p-6 bg-gradient-to-br from-green-50 to-green-100 border-green-200">
            <p class="text-sm text-green-600 font-medium">Finished Goods</p>
            <p class="text-2xl font-bold text-green-800">₹{{ formatNumber(inventoryData.finished_goods?.total_value || 0) }}</p>
          </div>
          <div class="card p-6 bg-gradient-to-br from-purple-50 to-purple-100 border-purple-200">
            <p class="text-sm text-purple-600 font-medium">Grand Total</p>
            <p class="text-2xl font-bold text-purple-800">₹{{ formatNumber(inventoryData.grand_total || 0) }}</p>
          </div>
        </div>
        
        <!-- Pie Chart -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="card p-4">
            <h4 class="text-sm font-medium text-gray-700 mb-4">Inventory Composition</h4>
            <canvas ref="inventoryChart" height="200"></canvas>
          </div>
          <div class="card p-4">
            <h4 class="text-sm font-medium text-gray-700 mb-4">Breakdown</h4>
            <div class="space-y-3">
              <div v-for="item in inventoryData.raw_materials?.items || []" :key="item.type" class="flex justify-between">
                <span class="text-gray-600">{{ item.type }}</span>
                <span class="font-medium">{{ formatNumber(item.qty_kg) }} kg • ₹{{ formatNumber(item.value) }}</span>
              </div>
              <hr>
              <div v-for="item in inventoryData.finished_goods?.items || []" :key="item.type" class="flex justify-between">
                <span class="text-gray-600">{{ item.type }}</span>
                <span class="font-medium">{{ formatNumber(item.qty_litres) }} L • ₹{{ formatNumber(item.value) }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- DOWNTIME TAB -->
      <div v-if="activeTab === 'downtime'" class="space-y-6">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold">Downtime Analysis</h3>
          <button @click="exportCSV('downtime')" class="btn btn-secondary text-sm">📥 Download CSV</button>
        </div>
        
        <!-- Summary Card -->
        <div class="card p-6 bg-red-50 border-red-200">
          <p class="text-sm text-red-600 font-medium">Total Downtime ({{ period }})</p>
          <p class="text-3xl font-bold text-red-800">{{ downtimeData.total_downtime_hours || 0 }} hours</p>
        </div>
        
        <!-- Downtime Bar Chart -->
        <div class="card p-4">
          <canvas ref="downtimeChart" height="100"></canvas>
        </div>
        
        <!-- Reactor Table -->
        <div class="card">
          <table class="min-w-full divide-y divide-gray-200">
            <thead class="bg-gray-50">
              <tr>
                <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Reactor</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Maintenance Count</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Total Downtime (hrs)</th>
                <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Avg Downtime (hrs)</th>
              </tr>
            </thead>
            <tbody class="bg-white divide-y divide-gray-200">
              <tr v-for="r in downtimeData.reactors || []" :key="r.reactor_id" class="hover:bg-gray-50">
                <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ r.reactor_code }} - {{ r.reactor_name }}</td>
                <td class="px-4 py-3 text-sm text-right text-gray-500">{{ r.maintenance_count }}</td>
                <td class="px-4 py-3 text-sm text-right" :class="r.total_downtime_hours > 20 ? 'text-red-600 font-medium' : 'text-gray-500'">
                  {{ r.total_downtime_hours }}
                </td>
                <td class="px-4 py-3 text-sm text-right text-gray-500">{{ r.avg_downtime_hours }}</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      <!-- PRODUCTION TAB -->
      <div v-if="activeTab === 'production'" class="space-y-6">
        <h3 class="text-lg font-semibold">Production Summary</h3>
        
        <!-- KPI Cards -->
        <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div class="card p-4">
            <p class="text-xs text-gray-500 uppercase">Batches</p>
            <p class="text-2xl font-bold">{{ productionData.batches?.count || 0 }}</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-gray-500 uppercase">Input Processed</p>
            <p class="text-2xl font-bold">{{ formatNumber(productionData.batches?.total_input_kg || 0) }} kg</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-gray-500 uppercase">Avg Oil Yield</p>
            <p class="text-2xl font-bold" :class="getYieldColor(productionData.yields?.avg_oil_yield, productionData.yields?.target_oil_yield)">
              {{ productionData.yields?.avg_oil_yield || 0 }}%
            </p>
            <p class="text-xs text-gray-400">Target: {{ productionData.yields?.target_oil_yield }}%</p>
          </div>
          <div class="card p-4">
            <p class="text-xs text-gray-500 uppercase">Capacity Utilization</p>
            <p class="text-2xl font-bold">{{ productionData.utilization?.capacity_utilization_pct || 0 }}%</p>
          </div>
        </div>
        
        <!-- Syn-gas Alert -->
        <div v-if="productionData.syngas?.alert" class="card p-4 bg-red-50 border-red-300">
          <div class="flex items-center">
            <span class="text-2xl mr-3">⚠️</span>
            <div>
              <p class="font-medium text-red-800">Syn-gas Loss Alert</p>
              <p class="text-sm text-red-600">
                Loss is {{ productionData.syngas?.loss_percent }}% (threshold: {{ productionData.syngas?.threshold }}%)
                - Check for leaks!
              </p>
            </div>
          </div>
        </div>
        
        <!-- Output Summary -->
        <div class="card p-4">
          <h4 class="font-medium mb-4">Output Summary</h4>
          <div class="grid grid-cols-3 gap-4 text-center">
            <div>
              <p class="text-3xl font-bold text-blue-600">{{ formatNumber(productionData.outputs?.oil_litres || 0) }}</p>
              <p class="text-sm text-gray-500">Oil (litres)</p>
            </div>
            <div>
              <p class="text-3xl font-bold text-gray-700">{{ formatNumber(productionData.outputs?.carbon_kg || 0) }}</p>
              <p class="text-sm text-gray-500">Carbon (kg)</p>
            </div>
            <div>
              <p class="text-3xl font-bold text-gray-500">{{ formatNumber(productionData.outputs?.steel_kg || 0) }}</p>
              <p class="text-sm text-gray-500">Steel (kg)</p>
            </div>
          </div>
        </div>
      </div>

      <!-- FINANCIALS TAB (Admin Only) -->
      <div v-if="activeTab === 'financials' && isAdmin" class="space-y-6">
        <h3 class="text-lg font-semibold">Profitability Dashboard</h3>
        
        <!-- Big Number Cards -->
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <div class="card p-6 bg-gradient-to-br from-green-50 to-green-100 border-green-300">
            <p class="text-sm text-green-600 font-medium uppercase">Revenue</p>
            <p class="text-3xl font-bold text-green-800">₹{{ formatLakhs(profitData.revenue?.total || 0) }}</p>
            <p class="text-xs text-green-600">{{ profitData.revenue?.invoice_count || 0 }} invoices</p>
          </div>
          <div class="card p-6 bg-gradient-to-br from-red-50 to-red-100 border-red-300">
            <p class="text-sm text-red-600 font-medium uppercase">Total Costs</p>
            <p class="text-3xl font-bold text-red-800">₹{{ formatLakhs(profitData.costs?.total || 0) }}</p>
          </div>
          <div class="card p-6 bg-gradient-to-br from-blue-50 to-blue-100 border-blue-300">
            <p class="text-sm text-blue-600 font-medium uppercase">Operating Profit</p>
            <p class="text-3xl font-bold" :class="(profitData.profit?.operating_profit || 0) >= 0 ? 'text-blue-800' : 'text-red-800'">
              ₹{{ formatLakhs(profitData.profit?.operating_profit || 0) }}
            </p>
            <p class="text-xs text-blue-600">Margin: {{ profitData.profit?.margin_percent || 0 }}%</p>
          </div>
        </div>
        
        <!-- Cost Breakdown -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="card p-4">
            <h4 class="font-medium mb-4">Cost Breakdown</h4>
            <canvas ref="costChart" height="200"></canvas>
          </div>
          <div class="card p-4">
            <h4 class="font-medium mb-4">Cost Details</h4>
            <div class="space-y-3">
              <div class="flex justify-between items-center">
                <span class="text-gray-600">Raw Materials</span>
                <span class="font-medium text-gray-900">₹{{ formatNumber(profitData.costs?.raw_materials || 0) }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-600">Power ({{ formatNumber(profitData.costs?.power_kwh || 0) }} kWh)</span>
                <span class="font-medium text-gray-900">₹{{ formatNumber(profitData.costs?.power || 0) }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-600">Labor</span>
                <span class="font-medium text-gray-900">₹{{ formatNumber(profitData.costs?.labor || 0) }}</span>
              </div>
              <div class="flex justify-between items-center">
                <span class="text-gray-600">Maintenance Parts</span>
                <span class="font-medium text-gray-900">₹{{ formatNumber(profitData.costs?.maintenance_parts || 0) }}</span>
              </div>
              <hr>
              <div class="flex justify-between items-center pt-2">
                <span class="font-medium">Total Costs</span>
                <span class="font-bold text-red-600">₹{{ formatNumber(profitData.costs?.total || 0) }}</span>
              </div>
            </div>
            
            <div class="mt-6 pt-4 border-t">
              <p class="text-xs text-gray-400">Rates Applied:</p>
              <p class="text-xs text-gray-500">Electricity: ₹{{ profitData.rates_used?.electricity_per_kwh || 0 }}/kWh</p>
              <p class="text-xs text-gray-500">Labor: ₹{{ profitData.rates_used?.labor_per_hour || 0 }}/hr</p>
            </div>
          </div>
        </div>
      </div>

      <!-- SALES TAB -->
      <div v-if="activeTab === 'sales'" class="space-y-6">
        <div class="flex justify-between items-center">
          <h3 class="text-lg font-semibold">Sales Performance</h3>
          <button @click="exportCSV('sales')" class="btn btn-secondary text-sm">📥 Download CSV</button>
        </div>
        
        <!-- Top Customers -->
        <div class="card">
          <div class="p-4 border-b">
            <h4 class="font-medium">Top Customers</h4>
          </div>
          <div class="overflow-x-auto">
            <table class="min-w-full divide-y divide-gray-200">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Rank</th>
                  <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Customer</th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Orders</th>
                  <th class="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Revenue</th>
                </tr>
              </thead>
              <tbody class="bg-white divide-y divide-gray-200">
                <tr v-for="c in salesData.top_customers || []" :key="c.rank" class="hover:bg-gray-50">
                  <td class="px-4 py-3 text-sm">
                    <span :class="getRankBadge(c.rank)">{{ c.rank }}</span>
                  </td>
                  <td class="px-4 py-3 text-sm font-medium text-gray-900">{{ c.customer_name }}</td>
                  <td class="px-4 py-3 text-sm text-right text-gray-500">{{ c.order_count }}</td>
                  <td class="px-4 py-3 text-sm text-right font-medium text-green-600">₹{{ formatNumber(c.revenue) }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        
        <!-- Product Mix & Realization -->
        <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div class="card p-4">
            <h4 class="font-medium mb-4">Product Mix</h4>
            <div class="space-y-2">
              <div v-for="p in salesData.product_mix || []" :key="p.product" class="flex items-center">
                <div class="flex-1">
                  <div class="flex justify-between text-sm mb-1">
                    <span>{{ p.product }}</span>
                    <span>{{ p.pct }}%</span>
                  </div>
                  <div class="w-full bg-gray-200 rounded-full h-2">
                    <div class="bg-blue-600 h-2 rounded-full" :style="{width: p.pct + '%'}"></div>
                  </div>
                </div>
              </div>
            </div>
          </div>
          <div class="card p-4">
            <h4 class="font-medium mb-4">Avg Realization Rate (₹/unit)</h4>
            <div class="space-y-3">
              <div v-for="(rate, product) in salesData.avg_realization_rates || {}" :key="product" class="flex justify-between items-center">
                <span class="text-gray-600">{{ product }}</span>
                <span class="text-xl font-bold text-blue-600">₹{{ rate }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, nextTick, watch } from 'vue'
import { Chart, registerables } from 'chart.js'
import { reportsApi } from '../services/api'

Chart.register(...registerables)

// State
const loading = ref(true)
const period = ref('last_month')
const activeTab = ref('yield')

// Data
const yieldData = ref({ vendors: [] })
const inventoryData = ref({})
const downtimeData = ref({ reactors: [] })
const productionData = ref({})
const profitData = ref({})
const salesData = ref({})

// Chart refs
const yieldChart = ref(null)
const inventoryChart = ref(null)
const downtimeChart = ref(null)
const costChart = ref(null)
let chartInstances = {}

// User role
const user = computed(() => JSON.parse(localStorage.getItem('user') || '{}'))
const isAdmin = computed(() => user.value.role === 'ADMIN')

// Visible tabs based on role
const visibleTabs = computed(() => {
  const tabs = [
    { id: 'yield', name: 'Vendor Yield' },
    { id: 'inventory', name: 'Inventory' },
    { id: 'downtime', name: 'Downtime' },
    { id: 'production', name: 'Production' },
    { id: 'sales', name: 'Sales' }
  ]
  if (isAdmin.value) {
    tabs.push({ id: 'financials', name: '💰 Financials' })
  }
  return tabs
})

// Format helpers
const formatNumber = (num) => {
  if (num === null || num === undefined) return '0'
  return new Intl.NumberFormat('en-IN').format(Math.round(num))
}

const formatLakhs = (num) => {
  if (num >= 100000) {
    return (num / 100000).toFixed(2) + ' L'
  }
  return formatNumber(num)
}

const getRankBadge = (rank) => {
  if (rank === 1) return 'inline-flex items-center justify-center w-6 h-6 bg-yellow-400 text-white text-xs font-bold rounded-full'
  if (rank === 2) return 'inline-flex items-center justify-center w-6 h-6 bg-gray-400 text-white text-xs font-bold rounded-full'
  if (rank === 3) return 'inline-flex items-center justify-center w-6 h-6 bg-orange-400 text-white text-xs font-bold rounded-full'
  return 'inline-flex items-center justify-center w-6 h-6 bg-gray-200 text-gray-600 text-xs rounded-full'
}

const getYieldColor = (actual, target) => {
  if (!target) return 'text-gray-900'
  if (actual >= target) return 'text-green-600'
  if (actual >= target * 0.9) return 'text-yellow-600'
  return 'text-red-600'
}

// Load all data
const loadAllData = async () => {
  loading.value = true
  try {
    const [yield_, inv, down, prod, sales] = await Promise.all([
      reportsApi.getVendorYield(period.value),
      reportsApi.getInventoryValuation(),
      reportsApi.getDowntimeAnalysis(period.value),
      reportsApi.getProductionSummary(period.value),
      reportsApi.getSalesPerformance(period.value)
    ])
    
    yieldData.value = yield_.data
    inventoryData.value = inv.data
    downtimeData.value = down.data
    productionData.value = prod.data
    salesData.value = sales.data
    
    // Load profitability only for admin
    if (isAdmin.value) {
      try {
        const profit = await reportsApi.getProfitability(period.value)
        profitData.value = profit.data
      } catch (e) {
        console.error('Profitability access denied or error:', e)
      }
    }
    
    // Render charts after data loads
    await nextTick()
    renderCharts()
  } catch (e) {
    console.error('Error loading reports:', e)
  } finally {
    loading.value = false
  }
}

// Render charts
const renderCharts = () => {
  // Destroy existing charts
  Object.values(chartInstances).forEach(c => c?.destroy())
  
  // Yield bar chart
  if (yieldChart.value && yieldData.value.vendors?.length) {
    chartInstances.yield = new Chart(yieldChart.value, {
      type: 'bar',
      data: {
        labels: yieldData.value.vendors.map(v => v.vendor_name),
        datasets: [{
          label: 'Oil Yield %',
          data: yieldData.value.vendors.map(v => v.avg_oil_yield),
          backgroundColor: yieldData.value.vendors.map(v => 
            v.avg_oil_yield >= (yieldData.value.target_oil_yield || 42) ? '#10b981' : '#ef4444'
          )
        }]
      },
      options: {
        responsive: true,
        plugins: {
          legend: { display: false },
          title: { display: true, text: 'Oil Yield % by Vendor (Target: ' + (yieldData.value.target_oil_yield || 42) + '%)' }
        },
        scales: {
          y: { beginAtZero: true, max: 60 }
        }
      }
    })
  }
  
  // Inventory pie chart
  if (inventoryChart.value) {
    const items = [
      ...(inventoryData.value.raw_materials?.items || []),
      ...(inventoryData.value.finished_goods?.items || [])
    ]
    if (items.length) {
      chartInstances.inventory = new Chart(inventoryChart.value, {
        type: 'doughnut',
        data: {
          labels: items.map(i => i.type),
          datasets: [{
            data: items.map(i => i.value),
            backgroundColor: ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899']
          }]
        },
        options: {
          responsive: true,
          plugins: {
            legend: { position: 'bottom' }
          }
        }
      })
    }
  }
  
  // Downtime bar chart
  if (downtimeChart.value && downtimeData.value.reactors?.length) {
    chartInstances.downtime = new Chart(downtimeChart.value, {
      type: 'bar',
      data: {
        labels: downtimeData.value.reactors.map(r => r.reactor_code),
        datasets: [{
          label: 'Downtime (hours)',
          data: downtimeData.value.reactors.map(r => r.total_downtime_hours),
          backgroundColor: '#ef4444'
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { display: false } }
      }
    })
  }
  
  // Cost pie chart (admin only)
  if (costChart.value && profitData.value.costs) {
    chartInstances.cost = new Chart(costChart.value, {
      type: 'doughnut',
      data: {
        labels: ['Raw Materials', 'Power', 'Labor', 'Maintenance'],
        datasets: [{
          data: [
            profitData.value.costs.raw_materials || 0,
            profitData.value.costs.power || 0,
            profitData.value.costs.labor || 0,
            profitData.value.costs.maintenance_parts || 0
          ],
          backgroundColor: ['#3b82f6', '#f59e0b', '#10b981', '#8b5cf6']
        }]
      },
      options: {
        responsive: true,
        plugins: { legend: { position: 'bottom' } }
      }
    })
  }
}

// CSV Export
const exportCSV = async (type) => {
  try {
    let response
    if (type === 'vendor') response = await reportsApi.exportVendorYieldCSV(period.value)
    else if (type === 'downtime') response = await reportsApi.exportDowntimeCSV(period.value)
    else if (type === 'sales') response = await reportsApi.exportSalesCSV(period.value)
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `${type}_report_${new Date().toISOString().slice(0,10)}.csv`)
    document.body.appendChild(link)
    link.click()
    link.remove()
  } catch (e) {
    console.error('Export error:', e)
  }
}

// Watch tab changes to re-render charts
watch(activeTab, () => {
  nextTick(() => renderCharts())
})

onMounted(() => {
  loadAllData()
})
</script>
