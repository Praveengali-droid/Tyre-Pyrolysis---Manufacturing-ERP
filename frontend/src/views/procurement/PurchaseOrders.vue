<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Purchase Orders</h2>
        <p class="text-sm text-gray-500">Create and manage orders to suppliers</p>
      </div>
      <button @click="showCreateModal = true" class="btn btn-primary btn-lg">
        <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        New Purchase Order
      </button>
    </div>

    <!-- PO List -->
    <div class="card overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 table-dense">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">PO Number</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Vendor</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Order Date</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Qty (kg)</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Amount</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Actions</th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="po in purchaseOrders" :key="po.id" class="hover:bg-gray-50">
            <td class="px-4 py-3 font-medium text-gray-900">{{ po.po_number }}</td>
            <td class="px-4 py-3 text-gray-700">{{ getVendorName(po.vendor_id) }}</td>
            <td class="px-4 py-3 text-gray-600">{{ formatDate(po.order_date) }}</td>
            <td class="px-4 py-3 text-gray-900 font-medium">{{ getTotalQty(po).toLocaleString() }}</td>
            <td class="px-4 py-3 text-gray-900">₹{{ po.total_amount?.toLocaleString('en-IN', {minimumFractionDigits: 2}) }}</td>
            <td class="px-4 py-3">
              <span :class="getStatusBadge(po.status)" class="badge">{{ po.status }}</span>
            </td>
            <td class="px-4 py-3">
              <button 
                v-if="po.status === 'DRAFT'"
                @click="confirmPO(po.id)"
                class="text-green-600 hover:text-green-900 text-sm font-medium mr-3"
              >
                Confirm
              </button>
              <router-link 
                v-if="po.status === 'CONFIRMED' || po.status === 'PARTIALLY_RECEIVED'"
                :to="`/inward-entry?po=${po.id}`"
                class="text-blue-600 hover:text-blue-900 text-sm font-medium"
              >
                Receive
              </router-link>
            </td>
          </tr>
          
          <tr v-if="purchaseOrders.length === 0 && !loading">
            <td colspan="7" class="px-4 py-8 text-center text-gray-500">
              No purchase orders found. Create your first PO!
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Create PO Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showCreateModal = false"></div>
        
        <div class="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div class="px-6 py-4 border-b">
            <h3 class="text-lg font-medium text-gray-900">Create Purchase Order</h3>
          </div>
          
          <form @submit.prevent="createPO" class="px-6 py-4 space-y-4">
            <!-- Vendor Selection -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Select Vendor *</label>
              <select v-model="form.vendor_id" required class="mt-1 input input-lg">
                <option value="">-- Select Vendor --</option>
                <option v-for="v in vendors" :key="v.id" :value="v.id">
                  {{ v.name }} ({{ v.vendor_code }})
                </option>
              </select>
            </div>
            
            <!-- Dates -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Order Date *</label>
                <input v-model="form.order_date" type="date" required class="mt-1 input">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Expected Delivery</label>
                <input v-model="form.expected_delivery_date" type="date" class="mt-1 input">
              </div>
            </div>
            
            <!-- Line Items -->
            <div class="border-t pt-4">
              <div class="flex justify-between items-center mb-3">
                <h4 class="text-sm font-medium text-gray-900">Line Items</h4>
                <button type="button" @click="addLineItem" class="btn btn-secondary text-sm py-1 px-3">
                  + Add Item
                </button>
              </div>
              
              <div v-for="(item, index) in form.items" :key="index" class="bg-gray-50 rounded p-3 mb-3">
                <div class="grid grid-cols-4 gap-3">
                  <div class="col-span-2">
                    <label class="block text-xs text-gray-600">Material</label>
                    <input v-model="item.material_name" type="text" class="mt-1 input text-sm" placeholder="e.g., Mixed Truck Tyres">
                  </div>
                  <div>
                    <label class="block text-xs text-gray-600">Qty (kg) *</label>
                    <input v-model.number="item.ordered_qty_kg" type="number" required min="1" class="mt-1 input text-sm">
                  </div>
                  <div>
                    <label class="block text-xs text-gray-600">Rate/kg (₹) *</label>
                    <input v-model.number="item.rate_per_kg" type="number" required step="0.01" class="mt-1 input text-sm">
                  </div>
                </div>
                <div class="flex justify-between items-center mt-2">
                  <span class="text-sm text-gray-600">
                    Line Total: ₹{{ (item.ordered_qty_kg * item.rate_per_kg || 0).toLocaleString('en-IN') }}
                  </span>
                  <button 
                    v-if="form.items.length > 1"
                    type="button" 
                    @click="form.items.splice(index, 1)"
                    class="text-red-500 text-sm"
                  >
                    Remove
                  </button>
                </div>
              </div>
            </div>
            
            <!-- Notes -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Notes</label>
              <textarea v-model="form.notes" class="mt-1 input" rows="2"></textarea>
            </div>
            
            <!-- Actions -->
            <div class="flex justify-end space-x-3 pt-4 border-t">
              <button type="button" @click="showCreateModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ saving ? 'Creating...' : 'Create PO' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { vendorApi, purchaseOrderApi, rawMaterialApi } from '../../services/api'

const purchaseOrders = ref([])
const vendors = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateModal = ref(false)

const form = ref({
  vendor_id: '',
  order_date: new Date().toISOString().split('T')[0],
  expected_delivery_date: '',
  notes: '',
  items: [{ material_name: '', ordered_qty_kg: 5000, rate_per_kg: 8.00, raw_material_id: 1, gst_rate: 5 }]
})

const loadData = async () => {
  loading.value = true
  try {
    const [poRes, vendorRes] = await Promise.all([
      purchaseOrderApi.list(),
      vendorApi.list()
    ])
    purchaseOrders.value = poRes.data
    vendors.value = vendorRes.data.items || []
  } catch (e) {
    console.error('Failed to load data:', e)
  } finally {
    loading.value = false
  }
}

const getVendorName = (vendorId) => {
  const vendor = vendors.value.find(v => v.id === vendorId)
  return vendor?.name || 'Unknown'
}

const getTotalQty = (po) => {
  return po.items?.reduce((sum, item) => sum + (item.ordered_qty_kg || 0), 0) || 0
}

const formatDate = (dateStr) => {
  if (!dateStr) return '-'
  return new Date(dateStr).toLocaleDateString('en-IN')
}

const getStatusBadge = (status) => {
  const map = {
    'DRAFT': 'badge-warning',
    'CONFIRMED': 'badge-info',
    'PARTIALLY_RECEIVED': 'badge-info',
    'RECEIVED': 'badge-success',
    'CANCELLED': 'badge-danger'
  }
  return map[status] || 'badge-info'
}

const addLineItem = () => {
  form.value.items.push({ material_name: '', ordered_qty_kg: 5000, rate_per_kg: 8.00, raw_material_id: 1, gst_rate: 5 })
}

const createPO = async () => {
  saving.value = true
  try {
    await purchaseOrderApi.create({
      vendor_id: parseInt(form.value.vendor_id),
      order_date: form.value.order_date,
      expected_delivery_date: form.value.expected_delivery_date || null,
      notes: form.value.notes,
      items: form.value.items.map(i => ({
        raw_material_id: 1, // Default - can enhance later
        ordered_qty_kg: i.ordered_qty_kg,
        rate_per_kg: i.rate_per_kg,
        hsn_code: '4004',
        gst_rate: 5
      }))
    })
    showCreateModal.value = false
    form.value = {
      vendor_id: '',
      order_date: new Date().toISOString().split('T')[0],
      expected_delivery_date: '',
      notes: '',
      items: [{ material_name: '', ordered_qty_kg: 5000, rate_per_kg: 8.00 }]
    }
    loadData()
  } catch (e) {
    console.error('Failed to create PO:', e)
    alert('Error: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const confirmPO = async (poId) => {
  try {
    await purchaseOrderApi.confirm(poId)
    loadData()
  } catch (e) {
    console.error('Failed to confirm PO:', e)
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

onMounted(loadData)
</script>
