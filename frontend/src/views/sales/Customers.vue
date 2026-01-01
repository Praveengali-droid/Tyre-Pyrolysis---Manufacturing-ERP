<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Customers</h2>
        <p class="text-sm text-gray-500">Manage buyers of oil, carbon, and steel</p>
      </div>
      <button @click="showAddModal = true" class="btn btn-primary">+ Add Customer</button>
    </div>

    <div class="card">
      <div class="card-body p-0">
        <table class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left">Code</th>
              <th class="px-4 py-3 text-left">Name</th>
              <th class="px-4 py-3 text-left">Type</th>
              <th class="px-4 py-3 text-left">City</th>
              <th class="px-4 py-3 text-left">GST</th>
              <th class="px-4 py-3 text-left">Phone</th>
              <th class="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="c in customers" :key="c.id" class="border-t hover:bg-gray-50">
              <td class="px-4 py-3 font-medium">{{ c.customer_code }}</td>
              <td class="px-4 py-3">{{ c.name }}</td>
              <td class="px-4 py-3">
                <span :class="getTypeBadge(c.customer_type)">{{ c.customer_type }}</span>
              </td>
              <td class="px-4 py-3">{{ c.city || '-' }}</td>
              <td class="px-4 py-3">{{ c.gst_number || '-' }}</td>
              <td class="px-4 py-3">{{ c.phone || '-' }}</td>
              <td class="px-4 py-3">
                <button @click="viewLedger(c)" class="text-blue-600 hover:underline text-xs">View Ledger</button>
              </td>
            </tr>
            <tr v-if="customers.length === 0">
              <td colspan="7" class="px-4 py-8 text-center text-gray-500">No customers yet</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Customer Modal -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showAddModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-screen overflow-y-auto">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Add Customer</h3>
          <form @submit.prevent="addCustomer" class="space-y-4">
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Name *</label>
                <input v-model="form.name" type="text" required class="mt-1 input">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Type</label>
                <select v-model="form.customer_type" class="mt-1 input">
                  <option value="ALL">All Products</option>
                  <option value="CARBON_BUYER">Carbon Buyer</option>
                  <option value="STEEL_BUYER">Steel Buyer</option>
                  <option value="OIL_BUYER">Oil Buyer</option>
                </select>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Contact Person</label>
                <input v-model="form.contact_person" type="text" class="mt-1 input">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Phone</label>
                <input v-model="form.phone" type="text" class="mt-1 input">
              </div>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Email</label>
              <input v-model="form.email" type="email" class="mt-1 input">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Address</label>
              <textarea v-model="form.address" rows="2" class="mt-1 input"></textarea>
            </div>
            <div class="grid grid-cols-3 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">City</label>
                <input v-model="form.city" type="text" class="mt-1 input">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">State</label>
                <input v-model="form.state" type="text" class="mt-1 input">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Pincode</label>
                <input v-model="form.pincode" type="text" class="mt-1 input">
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">GST Number</label>
                <input v-model="form.gst_number" type="text" class="mt-1 input" placeholder="22AAAAA0000A1Z5">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">PAN Number</label>
                <input v-model="form.pan_number" type="text" class="mt-1 input">
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Payment Terms (Days)</label>
                <input v-model.number="form.payment_terms_days" type="number" class="mt-1 input">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Credit Limit (₹)</label>
                <input v-model.number="form.credit_limit" type="number" class="mt-1 input">
              </div>
            </div>
            <div class="flex justify-end space-x-3 pt-4">
              <button type="button" @click="showAddModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary">Add Customer</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Ledger Modal -->
    <div v-if="showLedgerModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showLedgerModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-3xl w-full p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Ledger: {{ ledgerData?.customer?.name }}</h3>
          <div class="grid grid-cols-3 gap-4 mb-6">
            <div class="bg-gray-100 p-3 rounded text-center">
              <p class="text-2xl font-bold">{{ ledgerData?.summary?.total_carbon_orders || 0 }}</p>
              <p class="text-xs text-gray-500">Carbon Orders</p>
            </div>
            <div class="bg-gray-100 p-3 rounded text-center">
              <p class="text-2xl font-bold">{{ ledgerData?.summary?.total_steel_orders || 0 }}</p>
              <p class="text-xs text-gray-500">Steel Orders</p>
            </div>
            <div class="bg-green-100 p-3 rounded text-center">
              <p class="text-2xl font-bold text-green-700">₹{{ (ledgerData?.summary?.total_amount || 0).toLocaleString() }}</p>
              <p class="text-xs text-gray-500">Total Business</p>
            </div>
          </div>
          <button @click="showLedgerModal = false" class="btn btn-secondary">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { salesApi } from '../../services/api'

const customers = ref([])
const showAddModal = ref(false)
const showLedgerModal = ref(false)
const ledgerData = ref(null)
const form = ref({
  name: '', customer_type: 'ALL', contact_person: '', phone: '', email: '',
  address: '', city: '', state: '', pincode: '', gst_number: '', pan_number: '',
  payment_terms_days: 30, credit_limit: 0
})

const loadCustomers = async () => {
  try {
    const res = await salesApi.listCustomers()
    customers.value = res.data
  } catch (e) {
    console.error('Failed to load customers:', e)
  }
}

const addCustomer = async () => {
  try {
    await salesApi.createCustomer(form.value)
    showAddModal.value = false
    form.value = {
      name: '', customer_type: 'ALL', contact_person: '', phone: '', email: '',
      address: '', city: '', state: '', pincode: '', gst_number: '', pan_number: '',
      payment_terms_days: 30, credit_limit: 0
    }
    loadCustomers()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const viewLedger = async (customer) => {
  try {
    const res = await salesApi.getCustomerLedger(customer.id)
    ledgerData.value = res.data
    showLedgerModal.value = true
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const getTypeBadge = (type) => {
  const map = {
    'ALL': 'px-2 py-1 text-xs rounded bg-blue-100 text-blue-700',
    'CARBON_BUYER': 'px-2 py-1 text-xs rounded bg-gray-200 text-gray-700',
    'STEEL_BUYER': 'px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-700',
    'OIL_BUYER': 'px-2 py-1 text-xs rounded bg-amber-100 text-amber-700'
  }
  return map[type] || map['ALL']
}

onMounted(loadCustomers)
</script>
