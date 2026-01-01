<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Sale Orders</h2>
        <p class="text-sm text-gray-500">Manage orders and dispatches</p>
      </div>
    </div>

    <!-- Status Filter Cards -->
    <div class="grid grid-cols-5 gap-4 mb-6">
      <div @click="filterStatus = 'ALL'" :class="filterStatus === 'ALL' ? 'ring-2 ring-blue-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition">
        <p class="text-2xl font-bold text-gray-700">{{ orders.length }}</p>
        <p class="text-xs text-gray-500">All Orders</p>
      </div>
      <div @click="filterStatus = 'CONFIRMED'" :class="filterStatus === 'CONFIRMED' ? 'ring-2 ring-blue-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-blue-50">
        <p class="text-2xl font-bold text-blue-600">{{ countByStatus('CONFIRMED') }}</p>
        <p class="text-xs text-gray-500">Confirmed</p>
      </div>
      <div @click="filterStatus = 'PARTIALLY_DISPATCHED'" :class="filterStatus === 'PARTIALLY_DISPATCHED' ? 'ring-2 ring-orange-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-orange-50">
        <p class="text-2xl font-bold text-orange-600">{{ countByStatus('PARTIALLY_DISPATCHED') }}</p>
        <p class="text-xs text-gray-500">Partial</p>
      </div>
      <div @click="filterStatus = 'DISPATCHED'" :class="filterStatus === 'DISPATCHED' ? 'ring-2 ring-purple-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-purple-50">
        <p class="text-2xl font-bold text-purple-600">{{ countByStatus('DISPATCHED') }}</p>
        <p class="text-xs text-gray-500">Dispatched</p>
      </div>
      <div @click="filterStatus = 'DELIVERED'" :class="filterStatus === 'DELIVERED' ? 'ring-2 ring-green-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-green-50">
        <p class="text-2xl font-bold text-green-600">{{ countByStatus('DELIVERED') }}</p>
        <p class="text-xs text-gray-500">Delivered</p>
      </div>
    </div>

    <!-- Orders Table -->
    <div class="card">
      <div class="card-body p-0">
        <table class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left">Order #</th>
              <th class="px-4 py-3 text-left">Date</th>
              <th class="px-4 py-3 text-left">Customer</th>
              <th class="px-4 py-3 text-left">Amount</th>
              <th class="px-4 py-3 text-left">Status</th>
              <th class="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="o in filteredOrders" :key="o.id" class="border-t hover:bg-gray-50">
              <td class="px-4 py-3 font-medium text-blue-600 cursor-pointer" @click="viewOrder(o)">{{ o.order_number }}</td>
              <td class="px-4 py-3">{{ o.order_date }}</td>
              <td class="px-4 py-3">{{ getCustomerName(o.customer_id) }}</td>
              <td class="px-4 py-3 text-green-600 font-medium">₹{{ o.total_amount?.toLocaleString() }}</td>
              <td class="px-4 py-3">
                <span :class="getStatusBadge(o.status)">{{ o.status?.replace('_', ' ') }}</span>
              </td>
              <td class="px-4 py-3 space-x-2">
                <button v-if="o.status !== 'DELIVERED' && o.status !== 'CANCELLED'" @click="openDispatchWizard(o)" class="text-purple-600 hover:underline text-xs font-medium">
                  + Dispatch
                </button>
                <button @click="viewOrder(o)" class="text-blue-600 hover:underline text-xs">View</button>
              </td>
            </tr>
            <tr v-if="filteredOrders.length === 0">
              <td colspan="6" class="px-4 py-8 text-center text-gray-500">No orders found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Order Detail Modal -->
    <div v-if="showOrderModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showOrderModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-4xl w-full p-6 max-h-screen overflow-y-auto">
          <div class="flex justify-between items-center mb-4">
            <h3 class="text-lg font-medium text-gray-900">{{ selectedOrder?.order_number }}</h3>
            <span :class="getStatusBadge(selectedOrder?.status)">{{ selectedOrder?.status }}</span>
          </div>
          
          <!-- Tabs -->
          <div class="flex space-x-4 mb-4 border-b">
            <button @click="orderTab = 'items'" :class="orderTab === 'items' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'" class="px-3 py-2">Items</button>
            <button @click="orderTab = 'dispatches'" :class="orderTab === 'dispatches' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'" class="px-3 py-2">Dispatches</button>
            <button @click="orderTab = 'documents'" :class="orderTab === 'documents' ? 'border-b-2 border-blue-500 text-blue-600' : 'text-gray-500'" class="px-3 py-2">Documents</button>
          </div>
          
          <!-- Items Tab -->
          <div v-if="orderTab === 'items'">
            <table class="w-full text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left">Product</th>
                  <th class="px-3 py-2 text-left">Ordered</th>
                  <th class="px-3 py-2 text-left">Dispatched</th>
                  <th class="px-3 py-2 text-left">Pending</th>
                  <th class="px-3 py-2 text-left">Rate</th>
                  <th class="px-3 py-2 text-left">Amount</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="item in orderPendingItems" :key="item.sale_order_item_id" class="border-t">
                  <td class="px-3 py-2">{{ item.product_name }}</td>
                  <td class="px-3 py-2">{{ item.ordered_quantity }} {{ item.unit }}</td>
                  <td class="px-3 py-2 text-green-600">{{ item.dispatched_quantity }}</td>
                  <td class="px-3 py-2" :class="item.pending_quantity > 0 ? 'text-orange-600 font-medium' : 'text-green-600'">
                    {{ item.pending_quantity }}
                  </td>
                  <td class="px-3 py-2">₹{{ item.rate }}</td>
                  <td class="px-3 py-2">₹{{ (item.ordered_quantity * item.rate).toLocaleString() }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- Dispatches Tab -->
          <div v-if="orderTab === 'dispatches'">
            <table class="w-full text-sm">
              <thead class="bg-gray-50">
                <tr>
                  <th class="px-3 py-2 text-left">DC #</th>
                  <th class="px-3 py-2 text-left">Date</th>
                  <th class="px-3 py-2 text-left">Truck</th>
                  <th class="px-3 py-2 text-left">Qty</th>
                  <th class="px-3 py-2 text-left">Status</th>
                  <th class="px-3 py-2 text-left">Actions</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="d in orderDispatches" :key="d.id" class="border-t">
                  <td class="px-3 py-2 font-medium">{{ d.dispatch_number }}</td>
                  <td class="px-3 py-2">{{ d.dispatch_date }}</td>
                  <td class="px-3 py-2">{{ d.truck_number || '-' }}</td>
                  <td class="px-3 py-2">{{ d.total_quantity }}</td>
                  <td class="px-3 py-2">
                    <span :class="getDispatchStatusBadge(d.status)">{{ d.status }}</span>
                  </td>
                  <td class="px-3 py-2 space-x-1">
                    <button v-if="d.status === 'PENDING'" @click="shipDispatch(d)" class="text-purple-600 hover:underline text-xs">Ship</button>
                    <button v-if="d.status === 'SHIPPED'" @click="deliverDispatch(d)" class="text-green-600 hover:underline text-xs">Deliver</button>
                    <button @click="viewDocument(d, 'dc')" class="text-blue-600 hover:underline text-xs">DC</button>
                    <button @click="viewDocument(d, 'gatepass')" class="text-gray-600 hover:underline text-xs">Gate Pass</button>
                    <button v-if="!d.has_invoice" @click="generateInvoice(d)" class="text-orange-600 hover:underline text-xs">Generate Invoice</button>
                    <button v-else @click="viewDocument(d, 'invoice')" class="text-green-600 hover:underline text-xs">Invoice</button>
                  </td>
                </tr>
                <tr v-if="orderDispatches.length === 0">
                  <td colspan="6" class="px-3 py-4 text-center text-gray-500">No dispatches yet</td>
                </tr>
              </tbody>
            </table>
          </div>
          
          <!-- Documents Tab -->
          <div v-if="orderTab === 'documents'" class="space-y-4">
            <div v-for="d in orderDispatches" :key="d.id" class="border rounded p-3">
              <div class="flex justify-between items-center">
                <div>
                  <p class="font-medium">{{ d.dispatch_number }}</p>
                  <p class="text-xs text-gray-500">{{ d.dispatch_date }}</p>
                </div>
                <div class="space-x-2">
                  <button @click="viewDocument(d, 'dc')" class="btn btn-secondary text-xs">📄 Challan</button>
                  <button @click="viewDocument(d, 'gatepass')" class="btn btn-secondary text-xs">🚪 Gate Pass</button>
                  <button v-if="d.has_invoice" @click="viewDocument(d, 'invoice')" class="btn btn-primary text-xs">📜 Invoice</button>
                </div>
              </div>
            </div>
          </div>
          
          <div class="mt-6 flex justify-end">
            <button @click="showOrderModal = false" class="btn btn-secondary">Close</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Create Dispatch Wizard Modal -->
    <div v-if="showDispatchWizard" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showDispatchWizard = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-screen overflow-y-auto">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Create Dispatch - {{ wizardOrder?.order_number }}</h3>
          
          <form @submit.prevent="createDispatch" class="space-y-4">
            <!-- Step 1: Select Items -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Select Items to Dispatch</label>
              <div class="space-y-2">
                <div v-for="item in wizardPendingItems" :key="item.sale_order_item_id" class="flex items-center justify-between bg-gray-50 p-3 rounded">
                  <div>
                    <p class="font-medium">{{ item.product_name }}</p>
                    <p class="text-xs text-gray-500">Pending: {{ item.pending_quantity }} {{ item.unit }} | Stock: {{ item.current_stock }}</p>
                  </div>
                  <div class="flex items-center space-x-2">
                    <input v-model.number="item.dispatch_qty" type="number" :min="0" :max="Math.min(item.pending_quantity, item.current_stock)" class="input w-24" placeholder="Qty">
                    <span class="text-sm text-gray-500">/ {{ item.pending_quantity }}</span>
                  </div>
                </div>
              </div>
              <p v-if="insufficientStockError" class="text-red-500 text-sm mt-2">{{ insufficientStockError }}</p>
            </div>
            
            <!-- Step 2: Truck Details -->
            <div class="border-t pt-4">
              <label class="block text-sm font-medium text-gray-700 mb-2">Truck Details</label>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-xs text-gray-500">Truck Number</label>
                  <input v-model="dispatchForm.truck_number" type="text" class="mt-1 input" placeholder="TS 00 AB 1234">
                </div>
                <div>
                  <label class="block text-xs text-gray-500">Driver Name</label>
                  <input v-model="dispatchForm.driver_name" type="text" class="mt-1 input">
                </div>
                <div>
                  <label class="block text-xs text-gray-500">Driver Phone</label>
                  <input v-model="dispatchForm.driver_phone" type="text" class="mt-1 input">
                </div>
                <div>
                  <label class="block text-xs text-gray-500">E-Way Bill No. (Optional)</label>
                  <input v-model="dispatchForm.eway_bill_number" type="text" class="mt-1 input" placeholder="e.g. 141234567890">
                </div>
                <div class="flex items-center col-span-2">
                  <input v-model="dispatchForm.is_returnable" type="checkbox" id="returnable" class="mr-2">
                  <label for="returnable" class="text-sm">Returnable (Pallets/Drums)</label>
                </div>
              </div>
            </div>
            
            <div class="flex justify-end space-x-3 pt-4">
              <button type="button" @click="showDispatchWizard = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Creating...' : 'Create Dispatch' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- Document Viewer Modal -->
    <div v-if="showDocumentModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showDocumentModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl w-full p-6" :class="documentData?.size === 'A5' ? 'max-w-md' : 'max-w-3xl'">
          
          <!-- Delivery Challan -->
          <div v-if="documentData?.document_type === 'DELIVERY_CHALLAN'" class="print-area">
            <div class="text-center border-b pb-4 mb-4">
              <h2 class="text-xl font-bold">DELIVERY CHALLAN</h2>
              <p class="text-sm text-gray-500">{{ documentData.dc_number }}</p>
            </div>
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p class="text-xs text-gray-500">Date</p>
                <p class="font-medium">{{ documentData.dc_date }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Sale Order</p>
                <p class="font-medium">{{ documentData.sale_order_number }}</p>
              </div>
            </div>
            <div class="mb-4">
              <p class="text-xs text-gray-500">Consignee</p>
              <p class="font-medium">{{ documentData.customer?.name }}</p>
              <p class="text-sm">{{ documentData.customer?.address }}</p>
            </div>
            <div class="grid grid-cols-3 gap-4 mb-4">
              <div>
                <p class="text-xs text-gray-500">Truck #</p>
                <p class="font-medium">{{ documentData.truck_number }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Driver</p>
                <p class="font-medium">{{ documentData.driver_name }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Phone</p>
                <p class="font-medium">{{ documentData.driver_phone }}</p>
              </div>
            </div>
            <table class="w-full text-sm border mb-4">
              <thead class="bg-gray-100">
                <tr>
                  <th class="px-2 py-1 text-left border">#</th>
                  <th class="px-2 py-1 text-left border">Description</th>
                  <th class="px-2 py-1 text-left border">HSN</th>
                  <th class="px-2 py-1 text-left border">Qty</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in documentData.items" :key="idx">
                  <td class="px-2 py-1 border">{{ idx + 1 }}</td>
                  <td class="px-2 py-1 border">{{ item.description }}</td>
                  <td class="px-2 py-1 border">{{ item.hsn_code }}</td>
                  <td class="px-2 py-1 border">{{ item.quantity }} {{ item.unit }}</td>
                </tr>
              </tbody>
            </table>
            <div class="text-right font-bold">Total: {{ documentData.total_quantity }} units</div>
          </div>
          
          <!-- Gate Pass -->
          <div v-if="documentData?.document_type === 'GATE_PASS'" class="print-area text-center">
            <h2 class="text-lg font-bold border-b pb-2 mb-4">GATE PASS</h2>
            <p class="text-xl font-bold mb-4">{{ documentData.gate_pass_number }}</p>
            <div class="text-left space-y-2 mb-4">
              <p><span class="text-gray-500">Date:</span> {{ documentData.date }} {{ documentData.time }}</p>
              <p><span class="text-gray-500">Truck:</span> <span class="font-bold">{{ documentData.truck_number }}</span></p>
              <p><span class="text-gray-500">Driver:</span> {{ documentData.driver_name }}</p>
              <p><span class="text-gray-500">Destination:</span> {{ documentData.destination }}</p>
              <p><span class="text-gray-500">Quantity:</span> <span class="font-bold">{{ documentData.total_quantity }} units</span></p>
              <p><span class="text-gray-500">DC Ref:</span> {{ documentData.dc_number }}</p>
            </div>
            <div class="border-2 p-2 inline-block">
              <span class="font-bold">{{ documentData.is_returnable ? '☑ RETURNABLE' : '☐ NON-RETURNABLE' }}</span>
              <p v-if="documentData.is_returnable" class="text-xs text-gray-500">{{ documentData.returnable_items }}</p>
            </div>
            <div class="mt-6 pt-4 border-t">
              <p class="text-xs text-gray-500">Security Signature: _________________</p>
            </div>
          </div>
          
          <!-- Tax Invoice -->
          <div v-if="documentData?.document_type === 'TAX_INVOICE'" class="print-area">
            <div class="text-center border-b pb-4 mb-4">
              <h2 class="text-xl font-bold">TAX INVOICE</h2>
              <p class="text-sm text-gray-500">{{ documentData.invoice_number }}</p>
            </div>
            <div class="grid grid-cols-2 gap-6 mb-4">
              <div class="border p-3">
                <p class="text-xs text-gray-500 font-medium">SELLER</p>
                <p class="font-bold">{{ documentData.seller?.name }}</p>
                <p class="text-sm">{{ documentData.seller?.address }}</p>
                <p class="text-sm"><span class="text-gray-500">GSTIN:</span> {{ documentData.seller?.gstin }}</p>
                <p class="text-sm"><span class="text-gray-500">State:</span> {{ documentData.seller?.state }} ({{ documentData.seller?.state_code }})</p>
              </div>
              <div class="border p-3">
                <p class="text-xs text-gray-500 font-medium">BUYER</p>
                <p class="font-bold">{{ documentData.buyer?.name }}</p>
                <p class="text-sm">{{ documentData.buyer?.address }}</p>
                <p class="text-sm"><span class="text-gray-500">GSTIN:</span> {{ documentData.buyer?.gstin || 'N/A' }}</p>
                <p class="text-sm"><span class="text-gray-500">State:</span> {{ documentData.buyer?.state }}</p>
              </div>
            </div>
            <div class="mb-4">
              <p class="text-sm"><span class="text-gray-500">Place of Supply:</span> <span class="font-medium">{{ documentData.place_of_supply }}</span></p>
              <p class="text-sm"><span class="text-gray-500">Invoice Date:</span> {{ documentData.invoice_date }}</p>
            </div>
            <table class="w-full text-sm border mb-4">
              <thead class="bg-gray-100">
                <tr>
                  <th class="px-2 py-1 text-left border">#</th>
                  <th class="px-2 py-1 text-left border">Description</th>
                  <th class="px-2 py-1 text-left border">HSN</th>
                  <th class="px-2 py-1 text-left border">Qty</th>
                  <th class="px-2 py-1 text-left border">Rate</th>
                  <th class="px-2 py-1 text-left border">Amount</th>
                  <th v-if="!documentData.is_inter_state" class="px-2 py-1 text-left border">CGST</th>
                  <th v-if="!documentData.is_inter_state" class="px-2 py-1 text-left border">SGST</th>
                  <th v-if="documentData.is_inter_state" class="px-2 py-1 text-left border">IGST</th>
                  <th class="px-2 py-1 text-left border">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in documentData.items" :key="idx">
                  <td class="px-2 py-1 border">{{ idx + 1 }}</td>
                  <td class="px-2 py-1 border">{{ item.description }}</td>
                  <td class="px-2 py-1 border">{{ item.hsn_code }}</td>
                  <td class="px-2 py-1 border">{{ item.quantity }}</td>
                  <td class="px-2 py-1 border">₹{{ item.rate }}</td>
                  <td class="px-2 py-1 border">₹{{ item.amount }}</td>
                  <td v-if="!documentData.is_inter_state" class="px-2 py-1 border">₹{{ item.cgst }}</td>
                  <td v-if="!documentData.is_inter_state" class="px-2 py-1 border">₹{{ item.sgst }}</td>
                  <td v-if="documentData.is_inter_state" class="px-2 py-1 border">₹{{ item.igst }}</td>
                  <td class="px-2 py-1 border font-medium">₹{{ item.total }}</td>
                </tr>
              </tbody>
            </table>
            <div class="text-right space-y-1">
              <p>Subtotal: ₹{{ documentData.totals?.subtotal?.toLocaleString() }}</p>
              <p v-if="!documentData.is_inter_state">CGST: ₹{{ documentData.totals?.cgst?.toLocaleString() }}</p>
              <p v-if="!documentData.is_inter_state">SGST: ₹{{ documentData.totals?.sgst?.toLocaleString() }}</p>
              <p v-if="documentData.is_inter_state">IGST: ₹{{ documentData.totals?.igst?.toLocaleString() }}</p>
              <p class="text-lg font-bold">Grand Total: ₹{{ documentData.totals?.grand_total?.toLocaleString() }}</p>
            </div>
          </div>
          
          <div class="mt-6 flex justify-end space-x-2">
            <button @click="printDocument" class="btn btn-primary">🖨️ Print</button>
            <button @click="showDocumentModal = false" class="btn btn-secondary">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { salesApi, quotationApi, dispatchApi } from '../../services/api'

const orders = ref([])
const customers = ref([])
const filterStatus = ref('ALL')
const showOrderModal = ref(false)
const showDispatchWizard = ref(false)
const showDocumentModal = ref(false)
const selectedOrder = ref(null)
const orderTab = ref('items')
const orderPendingItems = ref([])
const orderDispatches = ref([])
const wizardOrder = ref(null)
const wizardPendingItems = ref([])
const dispatchForm = ref({ truck_number: '', driver_name: '', driver_phone: '', eway_bill_number: '', is_returnable: false })
const saving = ref(false)
const insufficientStockError = ref('')
const documentData = ref(null)

const filteredOrders = computed(() => {
  if (filterStatus.value === 'ALL') return orders.value
  return orders.value.filter(o => o.status === filterStatus.value)
})

const countByStatus = (status) => orders.value.filter(o => o.status === status).length

const loadData = async () => {
  try {
    const [ordersRes, customersRes] = await Promise.all([
      quotationApi.listOrders(),
      salesApi.listCustomers()
    ])
    orders.value = ordersRes.data
    customers.value = customersRes.data
  } catch (e) {
    console.error('Failed to load data:', e)
  }
}

const getCustomerName = (id) => customers.value.find(c => c.id === id)?.name || '-'

const getStatusBadge = (status) => {
  const map = {
    'CONFIRMED': 'px-2 py-1 text-xs rounded bg-blue-100 text-blue-700',
    'PARTIALLY_DISPATCHED': 'px-2 py-1 text-xs rounded bg-orange-100 text-orange-700',
    'DISPATCHED': 'px-2 py-1 text-xs rounded bg-purple-100 text-purple-700',
    'DELIVERED': 'px-2 py-1 text-xs rounded bg-green-100 text-green-700',
    'CANCELLED': 'px-2 py-1 text-xs rounded bg-red-100 text-red-700'
  }
  return map[status] || 'px-2 py-1 text-xs rounded bg-gray-100 text-gray-600'
}

const getDispatchStatusBadge = (status) => {
  const map = {
    'PENDING': 'px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-700',
    'SHIPPED': 'px-2 py-1 text-xs rounded bg-purple-100 text-purple-700',
    'DELIVERED': 'px-2 py-1 text-xs rounded bg-green-100 text-green-700',
    'CANCELLED': 'px-2 py-1 text-xs rounded bg-red-100 text-red-700'
  }
  return map[status] || 'px-2 py-1 text-xs rounded bg-gray-100 text-gray-600'
}

const viewOrder = async (order) => {
  selectedOrder.value = order
  orderTab.value = 'items'
  showOrderModal.value = true
  
  // Load pending items and dispatches
  try {
    const [itemsRes, dispatchesRes] = await Promise.all([
      dispatchApi.getPendingItems(order.id),
      dispatchApi.list(order.id)
    ])
    orderPendingItems.value = itemsRes.data
    orderDispatches.value = dispatchesRes.data.map(d => ({ ...d, has_invoice: false }))
    
    // Check which dispatches have invoices
    for (const d of orderDispatches.value) {
      try {
        await dispatchApi.getInvoice(d.id)
        d.has_invoice = true
      } catch { d.has_invoice = false }
    }
  } catch (e) {
    console.error('Failed to load order details:', e)
  }
}

const openDispatchWizard = async (order) => {
  wizardOrder.value = order
  insufficientStockError.value = ''
  dispatchForm.value = { truck_number: '', driver_name: '', driver_phone: '', eway_bill_number: '', is_returnable: false }
  
  try {
    const res = await dispatchApi.getPendingItems(order.id)
    wizardPendingItems.value = res.data.map(item => ({ ...item, dispatch_qty: 0 }))
    showDispatchWizard.value = true
  } catch (e) {
    alert('Error loading pending items: ' + (e.response?.data?.detail || e.message))
  }
}

const createDispatch = async () => {
  // Validate at least one item
  const itemsToDispatch = wizardPendingItems.value.filter(i => i.dispatch_qty > 0)
  if (itemsToDispatch.length === 0) {
    alert('Please select at least one item to dispatch')
    return
  }
  
  // Check stock
  for (const item of itemsToDispatch) {
    if (item.dispatch_qty > item.current_stock) {
      insufficientStockError.value = `Insufficient stock for ${item.product_name}: requested ${item.dispatch_qty}, available ${item.current_stock}`
      return
    }
  }
  
  saving.value = true
  insufficientStockError.value = ''
  
  try {
    await dispatchApi.create({
      sale_order_id: wizardOrder.value.id,
      truck_number: dispatchForm.value.truck_number,
      driver_name: dispatchForm.value.driver_name,
      driver_phone: dispatchForm.value.driver_phone,
      eway_bill_number: dispatchForm.value.eway_bill_number || null,
      is_returnable: dispatchForm.value.is_returnable,
      items: itemsToDispatch.map(i => ({
        sale_order_item_id: i.sale_order_item_id,
        product_id: i.product_id,
        quantity: i.dispatch_qty,
        rate: i.rate
      }))
    })
    showDispatchWizard.value = false
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const shipDispatch = async (dispatch) => {
  try {
    await dispatchApi.ship(dispatch.id)
    viewOrder(selectedOrder.value)
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const deliverDispatch = async (dispatch) => {
  try {
    await dispatchApi.deliver(dispatch.id)
    viewOrder(selectedOrder.value)
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const generateInvoice = async (dispatch) => {
  try {
    await dispatchApi.generateInvoice(dispatch.id)
    viewOrder(selectedOrder.value)
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const viewDocument = async (dispatch, type) => {
  try {
    let res
    if (type === 'dc') res = await dispatchApi.getDeliveryChallan(dispatch.id)
    else if (type === 'gatepass') res = await dispatchApi.getGatePass(dispatch.id)
    else if (type === 'invoice') res = await dispatchApi.getInvoiceDocument(dispatch.id)
    
    documentData.value = res.data
    showDocumentModal.value = true
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const printDocument = () => {
  window.print()
}

onMounted(loadData)
</script>

<style>
@media print {
  body * { visibility: hidden; }
  .print-area, .print-area * { visibility: visible; }
  .print-area { position: absolute; left: 0; top: 0; width: 100%; }
}
</style>
