<template>
  <div class="max-w-4xl mx-auto">
    <!-- Form Header -->
    <div class="mb-6">
      <h2 class="text-xl font-semibold text-gray-900">Record Truck Arrival</h2>
      <p class="text-sm text-gray-500">Enter weights and deductions to calculate payable amount</p>
    </div>

    <form @submit.prevent="submitEntry">
      <!-- Vehicle & Vendor Info -->
      <div class="card mb-6">
        <div class="card-header bg-gray-50">
          <h3 class="text-sm font-medium text-gray-900">Vehicle & Vendor Details</h3>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Vehicle Number *</label>
              <input 
                v-model="form.vehicle_number" 
                type="text" 
                required 
                class="mt-1 input input-lg font-mono uppercase"
                placeholder="MH 12 AB 1234"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Driver Name</label>
              <input v-model="form.driver_name" type="text" class="mt-1 input">
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Driver Phone</label>
              <input v-model="form.driver_phone" type="tel" class="mt-1 input">
            </div>
          </div>
          
          <div class="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Select Vendor *</label>
              <select v-model="form.vendor_id" required class="mt-1 input input-lg">
                <option value="">-- Select Vendor --</option>
                <option v-for="v in vendors" :key="v.id" :value="v.id">
                  {{ v.name }} ({{ v.vendor_code }})
                </option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Material Description</label>
              <input v-model="form.material_description" type="text" class="mt-1 input" placeholder="e.g., Mixed Truck Tyres">
            </div>
          </div>
        </div>
      </div>

      <!-- Weight Entry -->
      <div class="card mb-6">
        <div class="card-header bg-blue-50">
          <h3 class="text-sm font-medium text-blue-900">Weighbridge Data</h3>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Gross Weight (kg) *</label>
              <input 
                v-model.number="form.gross_weight_kg" 
                type="number" 
                step="0.01"
                min="0"
                required 
                @input="calculateWeights"
                class="input input-lg text-2xl font-bold text-center"
              >
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">Tare Weight (kg) *</label>
              <input 
                v-model.number="form.tare_weight_kg" 
                type="number" 
                step="0.01"
                min="0"
                required 
                @input="calculateWeights"
                class="input input-lg text-2xl font-bold text-center"
              >
            </div>
            
            <div class="bg-green-50 rounded-lg p-4 flex flex-col justify-center items-center">
              <label class="block text-sm font-medium text-green-700 mb-1">Net Weight</label>
              <span class="weight-display-lg weight-positive">{{ netWeight.toFixed(2) }}</span>
              <span class="text-sm text-green-600">kg</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Deductions -->
      <div class="card mb-6">
        <div class="card-header bg-red-50 flex justify-between items-center">
          <h3 class="text-sm font-medium text-red-900">Deductions (Mud / Water / Rims)</h3>
          <button 
            type="button"
            @click="addDeduction"
            :disabled="form.deductions.length >= 3"
            class="btn btn-secondary text-sm py-1 px-3"
          >
            + Add Deduction
          </button>
        </div>
        <div class="card-body">
          <div v-if="form.deductions.length === 0" class="text-center py-4 text-gray-500">
            No deductions. Click "Add Deduction" if needed.
          </div>
          
          <div v-for="(deduction, index) in form.deductions" :key="index" class="flex gap-4 items-end mb-4">
            <div class="flex-1">
              <label class="block text-sm font-medium text-gray-700">Deduction Type</label>
              <select v-model="deduction.type" required class="mt-1 input">
                <option value="MUD">Mud</option>
                <option value="WATER">Water / Wet Tyres</option>
                <option value="RIMS">Steel Rims</option>
                <option value="SAND">Sand / Gravel</option>
                <option value="FOREIGN_MATERIAL">Foreign Material</option>
                <option value="OTHER">Other</option>
              </select>
            </div>
            
            <div class="w-40">
              <label class="block text-sm font-medium text-gray-700">Weight (kg)</label>
              <input 
                v-model.number="deduction.weight_kg" 
                type="number" 
                step="0.01"
                min="0"
                required
                @input="calculateWeights"
                class="mt-1 input text-lg font-bold text-red-600"
              >
            </div>
            
            <div class="flex-1">
              <label class="block text-sm font-medium text-gray-700">Reason</label>
              <input v-model="deduction.reason" type="text" class="mt-1 input" placeholder="Optional notes">
            </div>
            
            <button 
              type="button"
              @click="removeDeduction(index)"
              class="mb-1 text-red-500 hover:text-red-700 p-2"
            >
              <svg class="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
              </svg>
            </button>
          </div>
          
          <!-- Total Deduction -->
          <div v-if="form.deductions.length > 0" class="border-t pt-4 mt-4">
            <div class="flex justify-end items-center">
              <span class="text-sm font-medium text-gray-700 mr-4">Total Deduction:</span>
              <span class="text-2xl font-bold text-red-600">-{{ totalDeduction.toFixed(2) }} kg</span>
            </div>
          </div>
        </div>
      </div>

      <!-- Rate & GST -->
      <div class="card mb-6">
        <div class="card-header bg-gray-50">
          <h3 class="text-sm font-medium text-gray-900">Rate & Payment</h3>
        </div>
        <div class="card-body">
          <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Rate per kg (₹) *</label>
              <input 
                v-model.number="form.rate_per_kg" 
                type="number" 
                step="0.01"
                min="0"
                required
                @input="calculateWeights"
                class="mt-1 input input-lg text-xl font-bold"
              >
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">GST Rate (%)</label>
              <select v-model.number="form.gst_rate" @change="calculateWeights" class="mt-1 input input-lg">
                <option :value="0">0% (Exempt)</option>
                <option :value="5">5%</option>
                <option :value="12">12%</option>
                <option :value="18">18%</option>
              </select>
            </div>
            <div>
              <label class="block text-sm font-medium text-gray-700">Quality Grade</label>
              <select v-model="form.quality_grade" class="mt-1 input input-lg">
                <option value="">-- Select --</option>
                <option value="A">Grade A (Premium)</option>
                <option value="B">Grade B (Standard)</option>
                <option value="C">Grade C (Low Quality)</option>
              </select>
            </div>
          </div>
        </div>
      </div>

      <!-- Calculation Summary - BIG AND CLEAR -->
      <div class="card mb-6 border-2 border-green-500">
        <div class="card-header bg-green-600 text-white">
          <h3 class="text-lg font-bold">Payment Calculation Summary</h3>
        </div>
        <div class="card-body bg-green-50">
          <div class="grid grid-cols-2 md:grid-cols-4 gap-4 text-center">
            <div>
              <p class="text-sm text-gray-600">Net Weight</p>
              <p class="text-2xl font-bold text-gray-900">{{ netWeight.toFixed(2) }}</p>
              <p class="text-xs text-gray-500">kg (Physical Stock)</p>
            </div>
            
            <div>
              <p class="text-sm text-gray-600">Less: Deductions</p>
              <p class="text-2xl font-bold text-red-600">-{{ totalDeduction.toFixed(2) }}</p>
              <p class="text-xs text-gray-500">kg</p>
            </div>
            
            <div class="bg-white rounded-lg p-3 border-2 border-green-400">
              <p class="text-sm text-green-700 font-medium">Payable Weight</p>
              <p class="text-4xl font-extrabold text-green-600">{{ payableWeight.toFixed(2) }}</p>
              <p class="text-xs text-green-600">kg (Financial Basis)</p>
            </div>
            
            <div class="bg-white rounded-lg p-3 border-2 border-blue-400">
              <p class="text-sm text-blue-700 font-medium">Net Payable</p>
              <p class="text-4xl font-extrabold text-blue-600">₹{{ netPayable.toLocaleString('en-IN', {minimumFractionDigits: 2}) }}</p>
              <p class="text-xs text-blue-600">incl. GST</p>
            </div>
          </div>
          
          <!-- Detailed Breakdown -->
          <div class="mt-4 pt-4 border-t border-green-200">
            <div class="flex flex-wrap justify-center gap-6 text-sm">
              <div><span class="text-gray-600">Taxable:</span> <span class="font-medium">₹{{ grossAmount.toLocaleString('en-IN', {minimumFractionDigits: 2}) }}</span></div>
              <div><span class="text-gray-600">GST ({{ form.gst_rate }}%):</span> <span class="font-medium">₹{{ gstAmount.toLocaleString('en-IN', {minimumFractionDigits: 2}) }}</span></div>
            </div>
          </div>
        </div>
      </div>

      <!-- Submit Button -->
      <div class="flex justify-end gap-4">
        <button type="button" @click="resetForm" class="btn btn-secondary btn-lg">
          Clear Form
        </button>
        <button 
          type="submit" 
          :disabled="saving || !isFormValid"
          class="btn btn-primary btn-lg px-8"
        >
          <svg v-if="saving" class="animate-spin -ml-1 mr-2 h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
            <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
          </svg>
          {{ saving ? 'Saving...' : 'Save Inward Entry' }}
        </button>
      </div>
    </form>

    <!-- Success Message -->
    <div v-if="successMessage" class="fixed bottom-4 right-4 bg-green-500 text-white px-6 py-4 rounded-lg shadow-lg">
      <div class="flex items-center">
        <svg class="w-6 h-6 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
        </svg>
        {{ successMessage }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { vendorApi, inwardApi } from '../../services/api'

const router = useRouter()
const vendors = ref([])
const saving = ref(false)
const successMessage = ref('')

const form = ref({
  vehicle_number: '',
  driver_name: '',
  driver_phone: '',
  vendor_id: '',
  material_description: '',
  gross_weight_kg: 0,
  tare_weight_kg: 0,
  rate_per_kg: 8.00,
  gst_rate: 5,
  quality_grade: '',
  deductions: []
})

// Computed values
const netWeight = computed(() => {
  return Math.max(0, (form.value.gross_weight_kg || 0) - (form.value.tare_weight_kg || 0))
})

const totalDeduction = computed(() => {
  return form.value.deductions.reduce((sum, d) => sum + (d.weight_kg || 0), 0)
})

const payableWeight = computed(() => {
  return Math.max(0, netWeight.value - totalDeduction.value)
})

const grossAmount = computed(() => {
  return payableWeight.value * (form.value.rate_per_kg || 0)
})

const gstAmount = computed(() => {
  return (grossAmount.value * (form.value.gst_rate || 0)) / 100
})

const netPayable = computed(() => {
  return grossAmount.value + gstAmount.value
})

const isFormValid = computed(() => {
  return form.value.vehicle_number && 
         form.value.vendor_id && 
         form.value.gross_weight_kg > 0 &&
         form.value.tare_weight_kg >= 0 &&
         form.value.rate_per_kg > 0 &&
         payableWeight.value > 0
})

// Methods
const loadVendors = async () => {
  try {
    const res = await vendorApi.list()
    vendors.value = res.data.items || []
  } catch (e) {
    console.error('Failed to load vendors:', e)
  }
}

const addDeduction = () => {
  if (form.value.deductions.length < 3) {
    form.value.deductions.push({
      type: 'MUD',
      weight_kg: 0,
      reason: ''
    })
  }
}

const removeDeduction = (index) => {
  form.value.deductions.splice(index, 1)
}

const calculateWeights = () => {
  // This triggers reactive recalculation
}

const resetForm = () => {
  form.value = {
    vehicle_number: '',
    driver_name: '',
    driver_phone: '',
    vendor_id: '',
    material_description: '',
    gross_weight_kg: 0,
    tare_weight_kg: 0,
    rate_per_kg: 8.00,
    gst_rate: 5,
    quality_grade: '',
    deductions: []
  }
}

const submitEntry = async () => {
  saving.value = true
  try {
    const payload = {
      ...form.value,
      vendor_id: parseInt(form.value.vendor_id)
    }
    
    const res = await inwardApi.create(payload)
    
    // Show success and redirect to GRN Approvals page
    successMessage.value = `GRN ${res.data.grn_number} created! Redirecting to approvals...`
    
    setTimeout(() => {
      router.push('/grn')
    }, 1500)
    
  } catch (e) {
    console.error('Failed to save entry:', e)
    alert('Error: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

onMounted(loadVendors)
</script>
