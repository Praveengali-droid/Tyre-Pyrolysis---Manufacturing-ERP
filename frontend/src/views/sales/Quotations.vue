<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Quotations</h2>
        <p class="text-sm text-gray-500">Create quotes, track status, convert to sale orders</p>
      </div>
      <button @click="openCreateModal" class="btn btn-primary">+ New Quotation</button>
    </div>

    <!-- Status Summary Cards -->
    <div class="grid grid-cols-6 gap-4 mb-6">
      <div @click="filterStatus = 'ALL'" :class="filterStatus === 'ALL' ? 'ring-2 ring-blue-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition">
        <p class="text-2xl font-bold text-gray-700">{{ quotations.length }}</p>
        <p class="text-xs text-gray-500">All</p>
      </div>
      <div @click="filterStatus = 'DRAFT'" :class="filterStatus === 'DRAFT' ? 'ring-2 ring-gray-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-gray-50">
        <p class="text-2xl font-bold text-gray-600">{{ countByStatus('DRAFT') }}</p>
        <p class="text-xs text-gray-500">Draft</p>
      </div>
      <div @click="filterStatus = 'SENT'" :class="filterStatus === 'SENT' ? 'ring-2 ring-blue-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-blue-50">
        <p class="text-2xl font-bold text-blue-600">{{ countByStatus('SENT') }}</p>
        <p class="text-xs text-gray-500">Sent</p>
      </div>
      <div @click="filterStatus = 'ACCEPTED'" :class="filterStatus === 'ACCEPTED' ? 'ring-2 ring-green-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-green-50">
        <p class="text-2xl font-bold text-green-600">{{ countByStatus('ACCEPTED') }}</p>
        <p class="text-xs text-gray-500">Accepted</p>
      </div>
      <div @click="filterStatus = 'CONVERTED'" :class="filterStatus === 'CONVERTED' ? 'ring-2 ring-purple-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-purple-50">
        <p class="text-2xl font-bold text-purple-600">{{ countByStatus('CONVERTED') }}</p>
        <p class="text-xs text-gray-500">Converted</p>
      </div>
      <div @click="filterStatus = 'REJECTED'" :class="filterStatus === 'REJECTED' ? 'ring-2 ring-red-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-red-50">
        <p class="text-2xl font-bold text-red-600">{{ countByStatus('REJECTED') }}</p>
        <p class="text-xs text-gray-500">Rejected</p>
      </div>
    </div>

    <!-- Quotations Table -->
    <div class="card">
      <div class="card-body p-0">
        <table class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left">Number</th>
              <th class="px-4 py-3 text-left">Date</th>
              <th class="px-4 py-3 text-left">Customer</th>
              <th class="px-4 py-3 text-left">Valid Until</th>
              <th class="px-4 py-3 text-left">Amount</th>
              <th class="px-4 py-3 text-left">Status</th>
              <th class="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="q in filteredQuotations" :key="q.id" class="border-t hover:bg-gray-50">
              <td class="px-4 py-3 font-medium">{{ q.quotation_number }}</td>
              <td class="px-4 py-3">{{ q.quotation_date }}</td>
              <td class="px-4 py-3">{{ getCustomerName(q.customer_id) }}</td>
              <td class="px-4 py-3">{{ q.valid_until || '-' }}</td>
              <td class="px-4 py-3 text-green-600 font-medium">₹{{ q.total_amount?.toLocaleString() }}</td>
              <td class="px-4 py-3">
                <span :class="getStatusBadge(q.status)">{{ q.status }}</span>
              </td>
              <td class="px-4 py-3 space-x-1">
                <button v-if="q.status === 'DRAFT'" @click="sendQuotation(q)" class="text-blue-600 hover:underline text-xs">Send</button>
                <button v-if="q.status === 'SENT'" @click="acceptQuotation(q)" class="text-green-600 hover:underline text-xs">Accept</button>
                <button v-if="q.status === 'SENT'" @click="rejectQuotation(q)" class="text-red-600 hover:underline text-xs">Reject</button>
                <button v-if="q.status === 'ACCEPTED'" @click="convertToOrder(q)" class="text-purple-600 hover:underline text-xs font-medium">→ Order</button>
              </td>
            </tr>
            <tr v-if="filteredQuotations.length === 0">
              <td colspan="7" class="px-4 py-8 text-center text-gray-500">No quotations found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Quotation Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showCreateModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-screen overflow-y-auto">
          <h3 class="text-lg font-medium text-gray-900 mb-4">New Quotation</h3>
          <form @submit.prevent="createQuotation" class="space-y-4">
            <!-- Customer -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Customer *</label>
              <select v-model="form.customer_id" required class="mt-1 input">
                <option value="">-- Select Customer --</option>
                <option v-for="c in customers" :key="c.id" :value="c.id">{{ c.name }} ({{ c.customer_code }})</option>
              </select>
            </div>
            
            <!-- Items -->
            <div>
              <div class="flex justify-between items-center">
                <label class="block text-sm font-medium text-gray-700">Items</label>
                <button type="button" @click="addItem" class="text-blue-600 text-xs hover:underline">+ Add Item</button>
              </div>
              <div class="mt-2 space-y-2">
                <div v-for="(item, index) in form.items" :key="index" class="flex items-center space-x-2 bg-gray-50 p-2 rounded">
                  <select v-model="item.product_id" required class="input w-1/3" @change="setRate(index)">
                    <option value="">Product</option>
                    <option v-for="p in products" :key="p.id" :value="p.id">{{ p.name }}</option>
                  </select>
                  <input v-model.number="item.quantity" type="number" placeholder="Qty" required min="1" class="input w-20">
                  <input v-model.number="item.rate" type="number" placeholder="Rate" required min="0" step="0.01" class="input w-24">
                  <span class="text-green-600 font-medium w-28">₹{{ ((item.quantity || 0) * (item.rate || 0)).toLocaleString() }}</span>
                  <button type="button" @click="removeItem(index)" class="text-red-500 hover:text-red-700">✕</button>
                </div>
              </div>
            </div>
            
            <!-- Total -->
            <div class="bg-green-50 p-3 rounded-lg text-right">
              <p class="text-sm text-gray-600">Subtotal: ₹{{ formSubtotal.toLocaleString() }}</p>
              <p class="text-sm text-gray-600">GST (18%): ₹{{ formTax.toLocaleString() }}</p>
              <p class="text-lg font-bold text-green-700">Total: ₹{{ formTotal.toLocaleString() }}</p>
            </div>
            
            <!-- Terms -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Valid Days</label>
                <input v-model.number="form.valid_days" type="number" class="mt-1 input" value="30">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Payment Terms</label>
                <input v-model="form.payment_terms" type="text" class="mt-1 input" placeholder="30 days credit">
              </div>
            </div>
            
            <div class="flex justify-end space-x-3 pt-4">
              <button type="button" @click="showCreateModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Creating...' : 'Create Quotation' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { salesApi, quotationApi } from '../../services/api'

const quotations = ref([])
const customers = ref([])
const products = ref([])
const filterStatus = ref('ALL')
const showCreateModal = ref(false)
const saving = ref(false)

const form = ref({
  customer_id: '',
  valid_days: 30,
  payment_terms: '',
  items: [{ product_id: '', quantity: 100, rate: 0 }]
})

const filteredQuotations = computed(() => {
  if (filterStatus.value === 'ALL') return quotations.value
  return quotations.value.filter(q => q.status === filterStatus.value)
})

const formSubtotal = computed(() => form.value.items.reduce((sum, i) => sum + (i.quantity || 0) * (i.rate || 0), 0))
const formTax = computed(() => Math.round(formSubtotal.value * 0.18))
const formTotal = computed(() => formSubtotal.value + formTax.value)

const countByStatus = (status) => quotations.value.filter(q => q.status === status).length

const loadData = async () => {
  try {
    const [quotRes, custRes, prodRes] = await Promise.all([
      quotationApi.list(),
      salesApi.listCustomers(),
      salesApi.listProducts()
    ])
    quotations.value = quotRes.data
    customers.value = custRes.data
    products.value = prodRes.data
  } catch (e) {
    console.error('Failed to load data:', e)
  }
}

const getCustomerName = (id) => customers.value.find(c => c.id === id)?.name || '-'

const getStatusBadge = (status) => {
  const map = {
    'DRAFT': 'px-2 py-1 text-xs rounded bg-gray-100 text-gray-600',
    'SENT': 'px-2 py-1 text-xs rounded bg-blue-100 text-blue-700',
    'ACCEPTED': 'px-2 py-1 text-xs rounded bg-green-100 text-green-700',
    'REJECTED': 'px-2 py-1 text-xs rounded bg-red-100 text-red-700',
    'CONVERTED': 'px-2 py-1 text-xs rounded bg-purple-100 text-purple-700',
    'EXPIRED': 'px-2 py-1 text-xs rounded bg-orange-100 text-orange-700'
  }
  return map[status] || map['DRAFT']
}

const openCreateModal = () => {
  form.value = {
    customer_id: '',
    valid_days: 30,
    payment_terms: '',
    items: [{ product_id: '', quantity: 100, rate: 0 }]
  }
  showCreateModal.value = true
}

const addItem = () => {
  form.value.items.push({ product_id: '', quantity: 100, rate: 0 })
}

const removeItem = (index) => {
  if (form.value.items.length > 1) form.value.items.splice(index, 1)
}

const setRate = (index) => {
  const product = products.value.find(p => p.id === form.value.items[index].product_id)
  if (product?.default_rate) form.value.items[index].rate = product.default_rate
}

const createQuotation = async () => {
  if (form.value.items.some(i => !i.product_id)) {
    alert('Please select a product for each item')
    return
  }
  saving.value = true
  try {
    await quotationApi.create(form.value)
    showCreateModal.value = false
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const sendQuotation = async (q) => {
  try {
    await quotationApi.send(q.id)
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const acceptQuotation = async (q) => {
  try {
    await quotationApi.accept(q.id)
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const rejectQuotation = async (q) => {
  try {
    await quotationApi.reject(q.id)
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const convertToOrder = async (q) => {
  try {
    await quotationApi.convert(q.id)
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(loadData)
</script>
