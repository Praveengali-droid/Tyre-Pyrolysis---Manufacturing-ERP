/**
 * User Store - Reactive global state for authenticated user.
 * 
 * This store maintains user state in both:
 * 1. Reactive ref (for Vue components to react to changes)
 * 2. localStorage (for persistence across page reloads)
 * 
 * Usage:
 *   import { useUserStore } from '@/stores/userStore'
 *   const { user, isAdmin, setUser, clearUser } = useUserStore()
 */
import { ref, computed, readonly } from 'vue'

// Reactive state (shared across all components)
const user = ref(JSON.parse(localStorage.getItem('user') || 'null'))
const token = ref(localStorage.getItem('token') || null)

/**
 * Set user after successful login.
 */
function setUser(userData, accessToken) {
    user.value = userData
    token.value = accessToken
    localStorage.setItem('user', JSON.stringify(userData))
    localStorage.setItem('token', accessToken)
}

/**
 * Clear user on logout.
 */
function clearUser() {
    user.value = null
    token.value = null
    localStorage.removeItem('user')
    localStorage.removeItem('token')
}

/**
 * Initialize from localStorage on app load.
 */
function initFromStorage() {
    const storedUser = localStorage.getItem('user')
    const storedToken = localStorage.getItem('token')
    if (storedUser && storedToken) {
        user.value = JSON.parse(storedUser)
        token.value = storedToken
    }
}

// Computed properties
const isLoggedIn = computed(() => !!user.value && !!token.value)
const isAdmin = computed(() => user.value?.role === 'ADMIN')
const isManager = computed(() => user.value?.role === 'MANAGER')
const canAccessReports = computed(() => ['ADMIN', 'MANAGER'].includes(user.value?.role))
const userRole = computed(() => user.value?.role || 'GUEST')
const userName = computed(() => user.value?.full_name || user.value?.username || 'Guest')
const userInitial = computed(() => (user.value?.username || 'G')[0].toUpperCase())

const userDisplayRole = computed(() => {
    const roleNames = {
        'ADMIN': 'Administrator',
        'MANAGER': 'Manager',
        'OPERATOR': 'Plant Operator',
        'VIEWER': 'Viewer'
    }
    return roleNames[userRole.value] || 'Guest'
})

/**
 * Composable hook for user store.
 */
export function useUserStore() {
    return {
        // State (readonly to prevent direct mutation)
        user: readonly(user),
        token: readonly(token),

        // Computed
        isLoggedIn,
        isAdmin,
        isManager,
        canAccessReports,
        userRole,
        userName,
        userInitial,
        userDisplayRole,

        // Actions
        setUser,
        clearUser,
        initFromStorage
    }
}
