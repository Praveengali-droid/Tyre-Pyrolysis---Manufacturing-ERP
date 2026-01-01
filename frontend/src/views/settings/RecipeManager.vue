<template>
  <div>
    <!-- Header -->
    <div class="flex justify-between items-center mb-6">
      <div>
        <h2 class="text-xl font-semibold text-gray-900">Recipe Manager</h2>
        <p class="text-sm text-gray-500">Configure production recipes and process stages</p>
      </div>
      <button @click="showCreateModal = true" class="btn btn-primary btn-lg">
        <svg class="w-5 h-5 mr-2" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4" />
        </svg>
        New Recipe
      </button>
    </div>

    <!-- Recipes List -->
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      <div 
        v-for="recipe in recipes" 
        :key="recipe.id"
        class="card cursor-pointer hover:shadow-lg transition-shadow"
        @click="viewRecipe(recipe.id)"
      >
        <div class="card-body">
          <div class="flex justify-between items-start mb-3">
            <div>
              <h3 class="text-lg font-semibold text-gray-900">{{ recipe.name }}</h3>
              <p class="text-sm text-gray-500">{{ recipe.recipe_code }}</p>
            </div>
            <span v-if="recipe.is_default" class="badge badge-success">Default</span>
          </div>
          
          <p class="text-sm text-gray-600 mb-4">{{ recipe.description || 'No description' }}</p>
          
          <div class="flex justify-between text-sm">
            <div>
              <span class="text-gray-500">Stages:</span>
              <span class="font-medium text-gray-900 ml-1">{{ recipe.stage_count }}</span>
            </div>
            <div>
              <span class="text-gray-500">Duration:</span>
              <span class="font-medium text-gray-900 ml-1">{{ formatDuration(recipe.total_duration_minutes) }}</span>
            </div>
          </div>
          
          <div v-if="recipe.tyre_type" class="mt-3">
            <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
              {{ recipe.tyre_type }}
            </span>
          </div>
        </div>
      </div>
      
      <!-- Empty State -->
      <div v-if="recipes.length === 0 && !loading" class="col-span-3 text-center py-12">
        <svg class="mx-auto h-12 w-12 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
        <h3 class="mt-2 text-sm font-medium text-gray-900">No recipes</h3>
        <p class="mt-1 text-sm text-gray-500">Get started by creating a new recipe.</p>
      </div>
    </div>

    <!-- Create Recipe Modal -->
    <div v-if="showCreateModal" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="showCreateModal = false"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
          <div class="px-6 py-4 border-b bg-green-50">
            <h3 class="text-lg font-medium text-green-900">Create New Recipe</h3>
          </div>
          
          <form @submit.prevent="createRecipe" class="px-6 py-4 space-y-6">
            <!-- Basic Info -->
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Recipe Code *</label>
                <input v-model="newRecipe.recipe_code" type="text" required class="mt-1 input" placeholder="RECIPE-RADIAL">
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700">Recipe Name *</label>
                <input v-model="newRecipe.name" type="text" required class="mt-1 input" placeholder="Radial Tyre Cycle">
              </div>
            </div>
            
            <div class="grid grid-cols-2 gap-4">
              <div>
                <label class="block text-sm font-medium text-gray-700">Tyre Type</label>
                <select v-model="newRecipe.tyre_type" class="mt-1 input">
                  <option value="">-- Select --</option>
                  <option value="Radial">Radial</option>
                  <option value="Nylon">Nylon</option>
                  <option value="Mixed">Mixed</option>
                  <option value="Industrial">Industrial</option>
                </select>
              </div>
              <div class="flex items-center mt-6">
                <input v-model="newRecipe.is_default" type="checkbox" class="h-4 w-4 text-green-600 rounded border-gray-300">
                <label class="ml-2 text-sm text-gray-700">Set as default recipe</label>
              </div>
            </div>
            
            <div>
              <label class="block text-sm font-medium text-gray-700">Description</label>
              <textarea v-model="newRecipe.description" rows="2" class="mt-1 input" placeholder="Standard process for radial tyres"></textarea>
            </div>
            
            <!-- Stages Section -->
            <div class="border-t pt-4">
              <div class="flex justify-between items-center mb-4">
                <h4 class="text-md font-medium text-gray-900">Process Stages</h4>
                <button type="button" @click="addStage" class="btn btn-secondary text-sm">+ Add Stage</button>
              </div>
              
              <div v-if="newRecipe.stages.length === 0" class="text-center py-4 text-gray-500 border border-dashed rounded-lg">
                No stages yet. Click "Add Stage" to define your process.
              </div>
              
              <div v-for="(stage, index) in newRecipe.stages" :key="index" class="mb-4 p-4 bg-gray-50 rounded-lg border">
                <div class="flex justify-between items-center mb-3">
                  <span class="text-sm font-medium text-gray-700">Stage {{ stage.order_sequence }}</span>
                  <button type="button" @click="removeStage(index)" class="text-red-500 hover:text-red-700 text-sm">Remove</button>
                </div>
                
                <div class="grid grid-cols-3 gap-4 mb-3">
                  <div>
                    <label class="block text-xs font-medium text-gray-600">Stage Name *</label>
                    <select v-model="stage.stage_name" required class="mt-1 input text-sm">
                      <option value="Loading">Loading</option>
                      <option value="Heating">Heating</option>
                      <option value="Distillation">Distillation</option>
                      <option value="Cooling">Cooling</option>
                      <option value="Unloading">Unloading</option>
                    </select>
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600">Duration (min) *</label>
                    <input v-model.number="stage.duration_minutes" type="number" required min="1" class="mt-1 input text-sm">
                  </div>
                  <div>
                    <label class="block text-xs font-medium text-gray-600">Required Readings</label>
                    <div class="mt-2 flex flex-wrap gap-2">
                      <label class="inline-flex items-center text-xs">
                        <input type="checkbox" v-model="stage.readingTemp" class="mr-1 rounded text-green-600">
                        Temp °C
                      </label>
                      <label class="inline-flex items-center text-xs">
                        <input type="checkbox" v-model="stage.readingPressure" class="mr-1 rounded text-green-600">
                        Pressure Bar
                      </label>
                      <label class="inline-flex items-center text-xs">
                        <input type="checkbox" v-model="stage.readingMeter" class="mr-1 rounded text-green-600">
                        Meter kWh
                      </label>
                    </div>
                  </div>
                </div>
                
                <!-- Safe Limits -->
                <div v-if="stage.readingTemp || stage.readingPressure" class="grid grid-cols-2 gap-4 mt-2">
                  <div v-if="stage.readingTemp" class="bg-white p-2 rounded border">
                    <label class="block text-xs font-medium text-gray-600 mb-1">Temp Safe Limits</label>
                    <div class="flex gap-2">
                      <input v-model.number="stage.tempMin" type="number" placeholder="Min" class="input text-xs w-20">
                      <span class="text-gray-400">-</span>
                      <input v-model.number="stage.tempMax" type="number" placeholder="Max" class="input text-xs w-20">
                      <span class="text-xs text-gray-500">°C</span>
                    </div>
                  </div>
                  <div v-if="stage.readingPressure" class="bg-white p-2 rounded border">
                    <label class="block text-xs font-medium text-gray-600 mb-1">Pressure Safe Max</label>
                    <div class="flex gap-2">
                      <input v-model.number="stage.pressureMax" type="number" step="0.1" placeholder="Max" class="input text-xs w-20">
                      <span class="text-xs text-gray-500">Bar</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            
            <div class="flex justify-end space-x-3 pt-4 border-t">
              <button type="button" @click="showCreateModal = false" class="btn btn-secondary">Cancel</button>
              <button type="submit" class="btn btn-primary" :disabled="saving">
                {{ saving ? 'Creating...' : 'Create Recipe' }}
              </button>
            </div>
          </form>
        </div>
      </div>
    </div>

    <!-- View Recipe Modal -->
    <div v-if="viewingRecipe" class="fixed inset-0 z-50 overflow-y-auto">
      <div class="flex items-center justify-center min-h-screen px-4">
        <div class="fixed inset-0 bg-gray-500 bg-opacity-75" @click="viewingRecipe = null"></div>
        <div class="relative bg-white rounded-lg shadow-xl max-w-3xl w-full">
          <div class="px-6 py-4 border-b bg-blue-50 flex justify-between items-center">
            <div>
              <h3 class="text-lg font-medium text-blue-900">{{ viewingRecipe.name }}</h3>
              <p class="text-sm text-blue-600">{{ viewingRecipe.recipe_code }}</p>
            </div>
            <button @click="viewingRecipe = null" class="text-gray-500 hover:text-gray-700">
              <svg class="w-6 h-6" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
          
          <div class="px-6 py-4">
            <div class="grid grid-cols-3 gap-4 text-center mb-6">
              <div class="bg-gray-50 p-3 rounded-lg">
                <p class="text-2xl font-bold text-gray-900">{{ viewingRecipe.stages?.length || 0 }}</p>
                <p class="text-xs text-gray-500">Stages</p>
              </div>
              <div class="bg-gray-50 p-3 rounded-lg">
                <p class="text-2xl font-bold text-gray-900">{{ formatDuration(viewingRecipe.total_duration_minutes) }}</p>
                <p class="text-xs text-gray-500">Total Duration</p>
              </div>
              <div class="bg-gray-50 p-3 rounded-lg">
                <p class="text-2xl font-bold text-gray-900">{{ viewingRecipe.tyre_type || 'Any' }}</p>
                <p class="text-xs text-gray-500">Tyre Type</p>
              </div>
            </div>
            
            <h4 class="text-sm font-semibold text-gray-700 mb-3">Process Timeline</h4>
            <div class="space-y-3">
              <div 
                v-for="(stage, idx) in viewingRecipe.stages" 
                :key="idx"
                class="flex items-start"
              >
                <div class="flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center text-white font-bold text-sm"
                  :class="getStageColor(stage.stage_name)">
                  {{ stage.order_sequence }}
                </div>
                <div class="ml-4 flex-1 bg-gray-50 rounded-lg p-3">
                  <div class="flex justify-between">
                    <span class="font-medium text-gray-900">{{ stage.stage_name }}</span>
                    <span class="text-sm text-gray-500">{{ stage.duration_minutes }} min</span>
                  </div>
                  <div v-if="stage.required_readings?.length" class="mt-1 text-xs text-gray-600">
                    Readings: {{ stage.required_readings.join(', ') }}
                  </div>
                  <div v-if="stage.safe_limits && Object.keys(stage.safe_limits).length" class="mt-1 text-xs text-orange-600">
                    Limits: {{ formatLimits(stage.safe_limits) }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { productionApi } from '../../services/api'

const recipes = ref([])
const loading = ref(false)
const saving = ref(false)
const showCreateModal = ref(false)
const viewingRecipe = ref(null)

const newRecipe = ref({
  recipe_code: '',
  name: '',
  description: '',
  tyre_type: '',
  is_default: false,
  stages: []
})

const loadRecipes = async () => {
  loading.value = true
  try {
    const res = await productionApi.listRecipes()
    recipes.value = res.data
  } catch (e) {
    console.error('Failed to load recipes:', e)
  } finally {
    loading.value = false
  }
}

const viewRecipe = async (id) => {
  try {
    const res = await productionApi.getRecipe(id)
    viewingRecipe.value = res.data
  } catch (e) {
    console.error('Failed to load recipe:', e)
  }
}

const addStage = () => {
  const seq = newRecipe.value.stages.length + 1
  const stageNames = ['Loading', 'Heating', 'Distillation', 'Cooling', 'Unloading']
  newRecipe.value.stages.push({
    stage_name: stageNames[Math.min(seq - 1, 4)],
    order_sequence: seq,
    duration_minutes: 60,
    readingTemp: false,
    readingPressure: false,
    readingMeter: false,
    tempMin: null,
    tempMax: null,
    pressureMax: null
  })
}

const removeStage = (index) => {
  newRecipe.value.stages.splice(index, 1)
  // Reorder
  newRecipe.value.stages.forEach((s, i) => s.order_sequence = i + 1)
}

const createRecipe = async () => {
  saving.value = true
  try {
    // Build stages payload
    const stages = newRecipe.value.stages.map(s => {
      const required_readings = []
      const safe_limits = {}
      
      if (s.readingTemp) {
        required_readings.push('temp_c')
        if (s.tempMin !== null || s.tempMax !== null) {
          safe_limits.temp_c = {}
          if (s.tempMin !== null) safe_limits.temp_c.min = s.tempMin
          if (s.tempMax !== null) safe_limits.temp_c.max = s.tempMax
        }
      }
      if (s.readingPressure) {
        required_readings.push('pressure_bar')
        if (s.pressureMax !== null) {
          safe_limits.pressure_bar = { max: s.pressureMax }
        }
      }
      if (s.readingMeter) required_readings.push('meter_kwh')
      
      return {
        stage_name: s.stage_name,
        order_sequence: s.order_sequence,
        duration_minutes: s.duration_minutes,
        required_readings,
        safe_limits,
        target_values: {},
        instructions: null
      }
    })
    
    await productionApi.createRecipe({
      recipe_code: newRecipe.value.recipe_code,
      name: newRecipe.value.name,
      description: newRecipe.value.description,
      tyre_type: newRecipe.value.tyre_type,
      is_default: newRecipe.value.is_default,
      stages
    })
    
    showCreateModal.value = false
    newRecipe.value = { recipe_code: '', name: '', description: '', tyre_type: '', is_default: false, stages: [] }
    loadRecipes()
  } catch (e) {
    alert('Error: ' + (e.response?.data?.detail || e.message))
  } finally {
    saving.value = false
  }
}

const formatDuration = (mins) => {
  if (!mins) return '0 min'
  const hours = Math.floor(mins / 60)
  const minutes = mins % 60
  if (hours === 0) return `${minutes} min`
  if (minutes === 0) return `${hours}h`
  return `${hours}h ${minutes}m`
}

const getStageColor = (name) => {
  const colors = {
    'Loading': 'bg-blue-500',
    'Heating': 'bg-red-500',
    'Distillation': 'bg-orange-500',
    'Cooling': 'bg-cyan-500',
    'Unloading': 'bg-green-500'
  }
  return colors[name] || 'bg-gray-500'
}

const formatLimits = (limits) => {
  const parts = []
  for (const [key, val] of Object.entries(limits)) {
    const name = key.replace('_c', '°C').replace('_bar', ' bar').replace('_kwh', ' kWh')
    if (val.min && val.max) parts.push(`${name}: ${val.min}-${val.max}`)
    else if (val.max) parts.push(`${name} max: ${val.max}`)
    else if (val.min) parts.push(`${name} min: ${val.min}`)
  }
  return parts.join(', ')
}

onMounted(loadRecipes)
</script>
