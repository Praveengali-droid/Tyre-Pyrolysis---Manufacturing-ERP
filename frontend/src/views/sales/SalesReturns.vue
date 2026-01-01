<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Sales Returns & RMA</h2>
        <p class="text-sm text-gray-500">Manage returns, QC, and credit notes</p>
      </div>
      <button @click="openReturnWizard" class="btn btn-primary">+ Create Return</button>
    </div>

    <!-- Status Filter Cards -->
    <div class="grid grid-cols-5 gap-4 mb-6">
      <div @click="filterStatus = 'ALL'" :class="filterStatus === 'ALL' ? 'ring-2 ring-blue-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition">
        <p class="text-2xl font-bold text-gray-700">{{ returns.length }}</p>
        <p class="text-xs text-gray-500">All Returns</p>
      </div>
      <div @click="filterStatus = 'PENDING'" :class="filterStatus === 'PENDING' ? 'ring-2 ring-yellow-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-yellow-50">
        <p class="text-2xl font-bold text-yellow-600">{{ countByStatus('PENDING') }}</p>
        <p class="text-xs text-gray-500">Pending</p>
      </div>
      <div @click="filterStatus = 'RECEIVED'" :class="filterStatus === 'RECEIVED' ? 'ring-2 ring-orange-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-orange-50">
        <p class="text-2xl font-bold text-orange-600">{{ countByStatus('RECEIVED') }}</p>
        <p class="text-xs text-gray-500">In QC</p>
      </div>
      <div @click="filterStatus = 'QC_PASS'" :class="filterStatus === 'QC_PASS' ? 'ring-2 ring-green-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-green-50">
        <p class="text-2xl font-bold text-green-600">{{ countByStatus('QC_PASS') }}</p>
        <p class="text-xs text-gray-500">QC Pass</p>
      </div>
      <div @click="filterStatus = 'QC_FAIL'" :class="filterStatus === 'QC_FAIL' ? 'ring-2 ring-red-500' : ''" class="card p-3 text-center cursor-pointer hover:shadow-md transition bg-red-50">
        <p class="text-2xl font-bold text-red-600">{{ countByStatus('QC_FAIL') }}</p>
        <p class="text-xs text-gray-500">QC Fail</p>
      </div>
    </div>

    <!-- Returns Table -->
    <div class="card">
      <div class="card-body p-0">
        <table class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left">RMA #</th>
              <th class="px-4 py-3 text-left">Date</th>
              <th class="px-4 py-3 text-left">Customer</th>
              <th class="px-4 py-3 text-left">Reason</th>
              <th class="px-4 py-3 text-left">Qty</th>
              <th class="px-4 py-3 text-left">Status</th>
              <th class="px-4 py-3 text-left">Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="r in filteredReturns" :key="r.id" class="border-t hover:bg-gray-50">
              <td class="px-4 py-3 font-medium text-blue-600">{{ r.return_number }}</td>
              <td class="px-4 py-3">{{ r.return_date }}</td>
              <td class="px-4 py-3">{{ getCustomerName(r.customer_id) }}</td>
              <td class="px-4 py-3">
                <span class="px-2 py-0.5 text-xs rounded" :class="getReasonBadge(r.reason_category)">{{ r.reason_category || 'OTHER' }}</span>
              </td>
              <td class="px-4 py-3">{{ r.total_quantity }}</td>
              <td class="px-4 py-3">
                <span :class="getStatusBadge(r.status)">{{ r.status?.replace('_', ' ') }}</span>
              </td>
              <td class="px-4 py-3 space-x-2">
                <button v-if="r.status === 'PENDING'" @click="receiveReturn(r)" class="text-orange-600 hover:underline text-xs">Receive</button>
                <button v-if="r.status === 'RECEIVED'" @click="openQCModal(r)" class="text-purple-600 hover:underline text-xs font-medium">QC Check</button>
                <button v-if="['QC_PASS', 'QC_FAIL'].includes(r.status)" @click="viewCreditNote(r)" class="text-green-600 hover:underline text-xs">Credit Note</button>
              </td>
            </tr>
            <tr v-if="filteredReturns.length === 0">
              <td colspan="7" class="px-4 py-8 text-center text-gray-500">No returns found</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Create Return Wizard Modal -->
    <div v-if="showReturnWizard" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showReturnWizard = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-2xl w-full p-6 max-h-screen overflow-y-auto">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Create Return (RMA)</h3>
          
          <form @submit.prevent="createReturn" class="space-y-4">
            <!-- Step 1: Select Invoice -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Select Invoice</label>
              <select v-model="selectedInvoiceId" @change="loadInvoiceItems" class="input w-full">
                <option value="">-- Select Invoice --</option>
                <option v-for="inv in invoices" :key="inv.id" :value="inv.id">{{ inv.invoice_number }}</option>
              </select>
            </div>
            
            <!-- Step 2: Select Items to Return -->
            <div v-if="returnableItems.length > 0">
              <label class="block text-sm font-medium text-gray-700 mb-2">Select Items to Return</label>
              <div class="space-y-2">
                <div v-for="item in returnableItems" :key="item.dispatch_item_id" class="flex items-center justify-between bg-gray-50 p-3 rounded">
                  <div>
                    <p class="font-medium">{{ item.product_name }}</p>
                    <p class="text-xs text-gray-500">Dispatched: {{ item.dispatched_quantity }} {{ item.unit }}</p>
                  </div>
                  <div class="flex items-center space-x-2">
                    <input v-model.number="item.return_qty" type="number" :min="0" :max="item.returnable_quantity" class="input w-24" placeholder="Qty">
                    <span class="text-sm text-gray-500">/ {{ item.returnable_quantity }}</span>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- Step 3: Reason -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-xs text-gray-500">Reason Category</label>
                <select v-model="returnForm.reason_category" class="mt-1 input w-full">
                  <option value="QUALITY">Quality Issue</option>
                  <option value="DAMAGE">Damaged Goods</option>
                  <option value="WRONG_PRODUCT">Wrong Product</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <div>
                <label class="block text-xs text-gray-500">Detailed Reason</label>
                <input v-model="returnForm.reason" type="text" class="mt-1 input w-full" placeholder="e.g. Material off-spec">
              </div>
            </div>
            
            <div class="flex justify-end space-x-3 pt-4">
              <button type="button" @click="showReturnWizard = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">{{ saving ? 'Creating...' : 'Create Return' }}</button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- QC Modal -->
    <div v-if="showQCModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showQCModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-lg w-full p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Quality Check - {{ qcReturn?.return_number }}</h3>
          
          <div class="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded">
            <p class="text-sm font-medium text-yellow-800">⚠️ Currently in QUARANTINE</p>
            <p class="text-xs text-yellow-600">Goods are held at {{ qcReturn?.quarantine_location }} location</p>
          </div>
          
          <div class="mb-4">
            <p class="text-sm text-gray-600"><strong>Reason:</strong> {{ qcReturn?.reason }}</p>
            <p class="text-sm text-gray-600"><strong>Quantity:</strong> {{ qcReturn?.total_quantity }} units</p>
          </div>
          
          <div class="mb-4">
            <label class="block text-xs text-gray-500">QC Notes (Optional)</label>
            <textarea v-model="qcNotes" rows="2" class="mt-1 input w-full" placeholder="Any observations..."></textarea>
          </div>
          
          <div class="flex justify-end space-x-3">
            <button @click="showQCModal = false" class="btn btn-secondary">Cancel</button>
            <button @click="handleQCFail" class="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700">
              ⚠️ Mark as Scrap
            </button>
            <button @click="handleQCPass" class="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700">
              ✅ Accept to Stock
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Credit Note Modal -->
    <div v-if="showCreditNoteModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showCreditNoteModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-3xl w-full p-6 max-h-screen overflow-y-auto">
          
          <div v-if="creditNoteData" class="print-area">
            <div class="text-center border-b pb-4 mb-4">
              <h2 class="text-xl font-bold text-red-600">CREDIT NOTE</h2>
              <p class="text-sm text-gray-500">{{ creditNoteData.credit_note_number }}</p>
            </div>
            
            <div class="grid grid-cols-2 gap-4 mb-4">
              <div>
                <p class="text-xs text-gray-500">Credit Note Date</p>
                <p class="font-medium">{{ creditNoteData.credit_note_date }}</p>
              </div>
              <div>
                <p class="text-xs text-gray-500">Original Invoice</p>
                <p class="font-medium">{{ creditNoteData.original_invoice_number }}</p>
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-6 mb-4">
              <div class="border p-3">
                <p class="text-xs text-gray-500 font-medium">SELLER</p>
                <p class="font-bold">{{ creditNoteData.seller?.name }}</p>
                <p class="text-sm">{{ creditNoteData.seller?.address }}</p>
                <p class="text-sm"><span class="text-gray-500">GSTIN:</span> {{ creditNoteData.seller?.gstin }}</p>
              </div>
              <div class="border p-3">
                <p class="text-xs text-gray-500 font-medium">BUYER</p>
                <p class="font-bold">{{ creditNoteData.buyer?.name }}</p>
                <p class="text-sm">{{ creditNoteData.buyer?.address }}</p>
                <p class="text-sm"><span class="text-gray-500">GSTIN:</span> {{ creditNoteData.buyer?.gstin || 'N/A' }}</p>
              </div>
            </div>
            
            <div class="mb-4 p-2 bg-yellow-50 border border-yellow-200">
              <p class="text-sm"><span class="text-gray-500">Reason for Credit:</span> <strong>{{ creditNoteData.reason }}</strong></p>
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
                  <th class="px-2 py-1 text-left border">Tax</th>
                  <th class="px-2 py-1 text-left border">Total</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="(item, idx) in creditNoteData.items" :key="idx">
                  <td class="px-2 py-1 border">{{ idx + 1 }}</td>
                  <td class="px-2 py-1 border">{{ item.description }}</td>
                  <td class="px-2 py-1 border">{{ item.hsn_code }}</td>
                  <td class="px-2 py-1 border">{{ item.quantity }}</td>
                  <td class="px-2 py-1 border">₹{{ item.rate }}</td>
                  <td class="px-2 py-1 border">₹{{ item.amount }}</td>
                  <td class="px-2 py-1 border">₹{{ item.cgst + item.sgst + item.igst }}</td>
                  <td class="px-2 py-1 border font-medium text-red-600">₹{{ item.total }}</td>
                </tr>
              </tbody>
            </table>
            
            <div class="text-right space-y-1">
              <p>Subtotal: <span class="text-red-600">₹{{ creditNoteData.totals?.subtotal?.toLocaleString() }}</span></p>
              <p v-if="!creditNoteData.is_inter_state">CGST: <span class="text-red-600">₹{{ creditNoteData.totals?.cgst?.toLocaleString() }}</span></p>
              <p v-if="!creditNoteData.is_inter_state">SGST: <span class="text-red-600">₹{{ creditNoteData.totals?.sgst?.toLocaleString() }}</span></p>
              <p v-if="creditNoteData.is_inter_state">IGST: <span class="text-red-600">₹{{ creditNoteData.totals?.igst?.toLocaleString() }}</span></p>
              <p class="text-lg font-bold">Credit Total: <span class="text-red-600">₹{{ creditNoteData.totals?.grand_total?.toLocaleString() }}</span></p>
            </div>
          </div>
          
          <div class="mt-6 flex justify-end space-x-2">
            <button @click="printDocument" class="btn btn-primary">🖨️ Print</button>
            <button @click="showCreditNoteModal = false" class="btn btn-secondary">Close</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { salesApi, dispatchApi, returnsApi } from '../../services/api'

const returns = ref([])
const customers = ref([])
const invoices = ref([])
const filterStatus = ref('ALL')
const showReturnWizard = ref(false)
const showQCModal = ref(false)
const showCreditNoteModal = ref(false)
const selectedInvoiceId = ref('')
const returnableItems = ref([])
const returnForm = ref({ reason: '', reason_category: 'QUALITY' })
const saving = ref(false)
const qcReturn = ref(null)
const qcNotes = ref('')
const creditNoteData = ref(null)

const filteredReturns = computed(() => {
  if (filterStatus.value === 'ALL') return returns.value
  return returns.value.filter(r => r.status === filterStatus.value)
})

const countByStatus = (status) => returns.value.filter(r => r.status === status).length

const loadData = async () => {
  try {
    const [returnsRes, customersRes] = await Promise.all([
      returnsApi.list(),
      salesApi.listCustomers()
    ])
    returns.value = returnsRes.data
    customers.value = customersRes.data
  } catch (e) {
    console.error('Failed to load data:', e)
  }
}

const loadInvoices = async () => {
  try {
    // Get dispatches that have invoices
    const dispRes = await dispatchApi.list()
    const dispatches = dispRes.data
    
    // For each dispatch with invoice, add to list
    invoices.value = []
    for (const d of dispatches) {
      try {
        const invRes = await dispatchApi.getInvoice(d.id)
        invoices.value.push({ id: invRes.data.id, invoice_number: invRes.data.invoice_number, dispatch_id: d.id })
      } catch { /* No invoice */ }
    }
  } catch (e) {
    console.error('Failed to load invoices:', e)
  }
}

const loadInvoiceItems = async () => {
  if (!selectedInvoiceId.value) {
    returnableItems.value = []
    return
  }
  try {
    const res = await returnsApi.getReturnableItems(selectedInvoiceId.value)
    returnableItems.value = res.data.items.map(i => ({ ...i, return_qty: 0 }))
  } catch (e) {
    alert('Error loading items: ' + (e.response?.data?.detail || e.message))
  }
}

const getCustomerName = (id) => customers.value.find(c => c.id === id)?.name || '-'

const getStatusBadge = (status) => {
  const map = {
    'PENDING': 'px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-700',
    'RECEIVED': 'px-2 py-1 text-xs rounded bg-orange-100 text-orange-700',
    'QC_PASS': 'px-2 py-1 text-xs rounded bg-green-100 text-green-700',
    'QC_FAIL': 'px-2 py-1 text-xs rounded bg-red-100 text-red-700',
    'CANCELLED': 'px-2 py-1 text-xs rounded bg-gray-100 text-gray-600'
  }
  return map[status] || 'px-2 py-1 text-xs rounded bg-gray-100 text-gray-600'
}

const getReasonBadge = (category) => {
  const map = {
    'QUALITY': 'bg-purple-100 text-purple-700',
    'DAMAGE': 'bg-red-100 text-red-700',
    'WRONG_PRODUCT': 'bg-orange-100 text-orange-700',
    'OTHER': 'bg-gray-100 text-gray-600'
  }
  return map[category] || 'bg-gray-100 text-gray-600'
}

const openReturnWizard = async () => {
  selectedInvoiceId.value = ''
  returnableItems.value = []
  returnForm.value = { reason: '', reason_category: 'QUALITY' }
  await loadInvoices()
  showReturnWizard.value = true
}

const createReturn = async () => {
  const itemsToReturn = returnableItems.value.filter(i => i.return_qty > 0)
  if (itemsToReturn.length === 0) {
    alert('Please select at least one item to return')
    return
  }
  
  saving.value = true
  try {
    await returnsApi.create({
      invoice_id: selectedInvoiceId.value,
      reason: returnForm.value.reason,
      reason_category: returnForm.value.reason_category,
      items: itemsToReturn.map(i => ({
        product_id: i.product_id,
        dispatch_item_id: i.dispatch_item_id,
        quantity: i.return_qty,
        rate: i.rate
      }))
    })
    showReturnWizard.value = false
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const receiveReturn = async (ret) => {
  try {
    await returnsApi.receive(ret.id)
    loadData()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const openQCModal = (ret) => {
  qcReturn.value = ret
  qcNotes.value = ''
  showQCModal.value = true
}

const handleQCPass = async () => {
  try {
    await returnsApi.qcPass(qcReturn.value.id, qcNotes.value)
    showQCModal.value = false
    loadData()
    alert('✅ QC Passed - Stock updated and Credit Note generated')
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const handleQCFail = async () => {
  try {
    await returnsApi.qcFail(qcReturn.value.id, qcNotes.value)
    showQCModal.value = false
    loadData()
    alert('⚠️ QC Failed - Goods moved to Scrap, Credit Note generated')
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const viewCreditNote = async (ret) => {
  try {
    const res = await returnsApi.getCreditNoteDocument(ret.id)
    creditNoteData.value = res.data
    showCreditNoteModal.value = true
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
