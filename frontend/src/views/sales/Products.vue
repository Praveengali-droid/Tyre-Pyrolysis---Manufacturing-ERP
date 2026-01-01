<template>
  <div>
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Products</h2>
        <p class="text-sm text-gray-500">Manage sellable products</p>
      </div>
      <button @click="showAddModal = true" class="btn btn-primary">+ Add Product</button>
    </div>

    <div class="card">
      <div class="card-body p-0">
        <table class="w-full text-sm">
          <thead class="bg-gray-50">
            <tr>
              <th class="px-4 py-3 text-left">Code</th>
              <th class="px-4 py-3 text-left">Name</th>
              <th class="px-4 py-3 text-left">Type</th>
              <th class="px-4 py-3 text-left">HSN</th>
              <th class="px-4 py-3 text-left">Unit</th>
              <th class="px-4 py-3 text-left">Rate</th>
              <th class="px-4 py-3 text-left">Stock</th>
              <th class="px-4 py-3 text-left">Status</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="p in products" :key="p.id" class="border-t hover:bg-gray-50">
              <td class="px-4 py-3 font-medium">{{ p.product_code }}</td>
              <td class="px-4 py-3">{{ p.name }}</td>
              <td class="px-4 py-3">
                <span :class="getTypeBadge(p.product_type)">{{ p.product_type }}</span>
              </td>
              <td class="px-4 py-3">{{ p.hsn_code || '-' }}</td>
              <td class="px-4 py-3">{{ p.unit }}</td>
              <td class="px-4 py-3">₹{{ p.default_rate?.toLocaleString() || '-' }}</td>
              <td class="px-4 py-3">{{ p.current_stock || 0 }}</td>
              <td class="px-4 py-3">
                <span v-if="p.is_active" class="text-green-600">Active</span>
                <span v-else class="text-gray-400">Inactive</span>
              </td>
            </tr>
            <tr v-if="products.length === 0">
              <td colspan="8" class="px-4 py-8 text-center text-gray-500">No products yet</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Add Product Modal -->
    <div v-if="showAddModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showAddModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-md w-full p-6">
          <h3 class="text-lg font-medium text-gray-900 mb-4">Add Product</h3>
          <form @submit.prevent="addProduct" class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Name *</label>
              <input v-model="form.name" type="text" required class="mt-1 input">
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Type *</label>
                <select v-model="form.product_type" required class="mt-1 input">
                  <option value="OIL">Oil</option>
                  <option value="CARBON">Carbon</option>
                  <option value="STEEL">Steel</option>
                  <option value="OTHER">Other</option>
                </select>
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Unit</label>
                <select v-model="form.unit" class="mt-1 input">
                  <option value="KG">KG</option>
                  <option value="LITERS">Liters</option>
                  <option value="NOS">Nos</option>
                </select>
              </div>
            </div>
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">HSN Code</label>
                <input v-model="form.hsn_code" type="text" class="mt-1 input">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Default Rate (₹)</label>
                <input v-model.number="form.default_rate" type="number" step="0.01" class="mt-1 input">
              </div>
            </div>
            <div class="flex justify-end space-x-3">
              <button type="button" @click="showAddModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary">Add Product</button>
            </div>
          </form>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { salesApi } from '../../services/api'

const products = ref([])
const showAddModal = ref(false)
const form = ref({ name: '', product_type: 'OTHER', unit: 'KG', hsn_code: '', default_rate: null })

const loadProducts = async () => {
  try {
    const res = await salesApi.listProducts()
    products.value = res.data
  } catch (e) {
    console.error('Failed to load products:', e)
  }
}

const addProduct = async () => {
  try {
    await salesApi.createProduct(form.value)
    showAddModal.value = false
    form.value = { name: '', product_type: 'OTHER', unit: 'KG', hsn_code: '', default_rate: null }
    loadProducts()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  }
}

const getTypeBadge = (type) => {
  const map = {
    'OIL': 'px-2 py-1 text-xs rounded bg-amber-100 text-amber-700',
    'CARBON': 'px-2 py-1 text-xs rounded bg-gray-200 text-gray-700',
    'STEEL': 'px-2 py-1 text-xs rounded bg-yellow-100 text-yellow-700',
    'OTHER': 'px-2 py-1 text-xs rounded bg-blue-100 text-blue-700'
  }
  return map[type] || map['OTHER']
}

onMounted(loadProducts)
</script>
