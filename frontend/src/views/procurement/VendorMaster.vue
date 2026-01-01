<template>
  <div>
    <!-- Header with Add Button -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Supplier List</h2>
        <p class="text-sm text-gray-500">Manage your scrap tyre suppliers with EPR compliance tracking</p>
      </div>
      <button 
        @click="showAddModal = true"
        class="btn btn-primary btn-lg"
      >
        <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        Add Vendor
      </button>
    </div>

    <!-- Filters -->
    <div class="card mb-4">
      <div class="card-body py-3">
        <div class="flex flex-wrap gap-4 items-center">
          <div class="flex-1 min-w-[200px]">
            <input
              v-model="search"
              type="text"
              placeholder="Search vendors..."
              class="input"
              @input="loadVendors"
            >
          </div>
          <div>
            <select v-model="eprFilter" @change="loadVendors" class="input">
              <option value="">All EPR Status</option>
              <option value="true">EPR Compliant</option>
              <option value="false">Non-Compliant</option>
            </select>
          </div>
        </div>
      </div>
    </div>
    
    <!-- Vendor Grid -->
    <div class="card overflow-hidden">
      <table class="min-w-full divide-y divide-gray-200 table-dense">
        <thead class="bg-gray-50">
          <tr>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Vendor
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Contact
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Location
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              GST Number
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              EPR Status
            </th>
            <th class="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
              Actions
            </th>
          </tr>
        </thead>
        <tbody class="bg-white divide-y divide-gray-200">
          <tr v-for="vendor in vendors" :key="vendor.id" class="hover:bg-gray-50">
            <td class="px-4 py-3">
              <div class="flex items-center">
                <div class="h-10 w-10 flex-shrink-0">
                  <div class="h-10 w-10 rounded-full bg-gray-200 flex items-center justify-center">
                    <span class="text-sm font-medium text-gray-600">
                      {{ vendor.name.charAt(0).toUpperCase() }}
                    </span>
                  </div>
                </div>
                <div class="ml-3">
                  <p class="text-sm font-medium text-gray-900">{{ vendor.name }}</p>
                  <p class="text-xs text-gray-500">{{ vendor.vendor_code }}</p>
                </div>
              </div>
            </td>
            <td class="px-4 py-3">
              <p class="text-sm text-gray-900">{{ vendor.contact_person || '-' }}</p>
              <p class="text-xs text-gray-500">{{ vendor.phone || '-' }}</p>
            </td>
            <td class="px-4 py-3">
              <p class="text-sm text-gray-900">{{ vendor.city || '-' }}</p>
              <p class="text-xs text-gray-500">{{ vendor.state || '-' }}</p>
            </td>
            <td class="px-4 py-3">
              <p class="text-sm font-mono text-gray-900">{{ vendor.gst_number || '-' }}</p>
            </td>
            <td class="px-4 py-3">
              <span 
                :class="getEprBadgeClass(vendor.epr_status)"
                class="badge"
              >
                {{ vendor.epr_status === 'COMPLIANT' ? '✓ EPR Compliant' : '✗ Non-Compliant' }}
              </span>
            </td>
            <td class="px-4 py-3">
              <button 
                @click="editVendor(vendor)"
                class="text-green-600 hover:text-green-900 text-sm font-medium"
              >
                Edit
              </button>
            </td>
          </tr>
          
          <!-- Empty State -->
          <tr v-if="vendors.length === 0 && !loading">
            <td colspan="6" class="px-4 py-8 text-center">
              <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
              <p class="mt-2 text-sm text-gray-500">No vendors found. Add your first supplier!</p>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Add/Edit Modal -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showAddModal = false"></div>
        
        <div class="relative bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
          <div class="px-6 py-4 border-b">
            <h3 class="text-lg font-medium text-gray-900">
              {{ editingVendor ? 'Edit Vendor' : 'Add New Vendor' }}
            </h3>
          </div>
          
          <form @submit.prevent="saveVendor" class="px-6 py-4 space-y-4">
            <!-- Basic Info -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Vendor Name *</label>
                <input v-model="form.name" type="text" required class="mt-1 input">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Contact Person</label>
                <input v-model="form.contact_person" type="text" class="mt-1 input">
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Phone</label>
                <input v-model="form.phone" type="tel" class="mt-1 input">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Email</label>
                <input v-model="form.email" type="email" class="mt-1 input">
              </div>
            </div>
            
            <!-- Address -->
            <div>
              <label class="block text-sm font-medium text-gray-700">Address</label>
              <input v-model="form.address_line1" type="text" class="mt-1 input" placeholder="Street address">
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
            
            <!-- GST Details -->
            <div class="border-t pt-4">
              <h4 class="text-sm font-medium text-gray-900 mb-3">GST Compliance</h4>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">GSTIN (15 characters)</label>
                  <input v-model="form.gst_number" type="text" maxlength="15" class="mt-1 input font-mono uppercase" placeholder="e.g., 27AAPFU0939F1ZV">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">GST Type</label>
                  <select v-model="form.gst_vendor_type" class="mt-1 input">
                    <option value="REGULAR">Regular</option>
                    <option value="COMPOSITION">Composition</option>
                    <option value="UNREGISTERED">Unregistered</option>
                    <option value="SEZ">SEZ</option>
                  </select>
                </div>
              </div>
            </div>
            
            <!-- EPR Compliance -->
            <div class="border-t pt-4">
              <h4 class="text-sm font-medium text-gray-900 mb-3">EPR Compliance (Extended Producer Responsibility)</h4>
              <div class="grid grid-cols-2 gap-4">
                <div>
                  <label class="block text-sm font-medium text-gray-700">EPC License Number</label>
                  <input v-model="form.epc_license_number" type="text" class="mt-1 input">
                </div>
                <div>
                  <label class="block text-sm font-medium text-gray-700">License Validity</label>
                  <input v-model="form.epc_validity_date" type="date" class="mt-1 input">
                </div>
              </div>
              <div class="mt-3">
                <label class="inline-flex items-center">
                  <input v-model="form.is_epr_compliant" type="checkbox" class="rounded border-gray-300 text-green-600 focus:ring-green-500">
                  <span class="ml-2 text-sm text-gray-700">Verified EPR Compliant</span>
                </label>
              </div>
            </div>
            
            <!-- Actions -->
            <div class="flex justify-end space-x-3 pt-4 border-t">
              <button type="button" @click="showAddModal = false" class="btn btn-secondary">
                Cancel
              </button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ saving ? 'Saving...' : (editingVendor ? 'Update Vendor' : 'Add Vendor') }}
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
import { vendorApi } from '../../services/api'

const vendors = ref([])
const loading = ref(false)
const saving = ref(false)
const showAddModal = ref(false)
const editingVendor = ref(null)
const search = ref('')
const eprFilter = ref('')

const form = ref({
  name: '',
  contact_person: '',
  phone: '',
  email: '',
  address_line1: '',
  city: '',
  state: '',
  pincode: '',
  gst_number: '',
  gst_vendor_type: 'REGULAR',
  epc_license_number: '',
  epc_validity_date: '',
  is_epr_compliant: false
})

const loadVendors = async () => {
  loading.value = true
  try {
    const params = { search: search.value }
    if (eprFilter.value) {
      params.epr_compliant = eprFilter.value === 'true'
    }
    const res = await vendorApi.list(params)
    vendors.value = res.data.items || []
  } catch (e) {
    console.error('Failed to load vendors:', e)
  } finally {
    loading.value = false
  }
}

const getEprBadgeClass = (status) => {
  return status === 'COMPLIANT' ? 'badge-success' : 'badge-danger'
}

const editVendor = (vendor) => {
  editingVendor.value = vendor
  form.value = { ...vendor }
  showAddModal.value = true
}

const resetForm = () => {
  form.value = {
    name: '',
    contact_person: '',
    phone: '',
    email: '',
    address_line1: '',
    city: '',
    state: '',
    pincode: '',
    gst_number: '',
    gst_vendor_type: 'REGULAR',
    epc_license_number: '',
    epc_validity_date: '',
    is_epr_compliant: false
  }
  editingVendor.value = null
}

const saveVendor = async () => {
  saving.value = true
  try {
    if (editingVendor.value) {
      await vendorApi.update(editingVendor.value.id, form.value)
    } else {
      await vendorApi.create(form.value)
    }
    showAddModal.value = false
    resetForm()
    loadVendors()
  } catch (e) {
    console.error('Failed to save vendor:', e)
    alert('Error saving vendor: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

onMounted(loadVendors)
</script>
