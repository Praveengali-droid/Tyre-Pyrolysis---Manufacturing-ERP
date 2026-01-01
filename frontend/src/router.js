import { createRouter, createWebHistory } from 'vue-router'

// Import views
import Dashboard from './views/Dashboard.vue'
import VendorMaster from './views/procurement/VendorMaster.vue'
import PurchaseOrders from './views/procurement/PurchaseOrders.vue'
import InwardEntry from './views/procurement/InwardEntry.vue'
import GrnList from './views/procurement/GrnList.vue'
import ControlRoom from './views/production/ControlRoom.vue'
import RecipeManager from './views/settings/RecipeManager.vue'
import Sales from './views/sales/Sales.vue'
import Products from './views/sales/Products.vue'
import Customers from './views/sales/Customers.vue'
import Dispatches from './views/sales/Dispatches.vue'
import Login from './views/Login.vue'

const routes = [
    // Public routes
    {
        path: '/login',
        name: 'Login',
        component: Login,
        meta: { requiresAuth: false }
    },
    // Protected routes
    {
        path: '/',
        name: 'Dashboard',
        component: Dashboard,
        meta: { requiresAuth: true }
    },
    // Procurement
    {
        path: '/vendors',
        name: 'VendorMaster',
        component: VendorMaster,
        meta: { requiresAuth: true, minRole: 'VIEWER' }
    },
    {
        path: '/purchase-orders',
        name: 'PurchaseOrders',
        component: PurchaseOrders,
        meta: { requiresAuth: true }
    },
    {
        path: '/inward-entry',
        name: 'InwardEntry',
        component: InwardEntry,
        meta: { requiresAuth: true, minRole: 'OPERATOR' }
    },
    {
        path: '/grn',
        name: 'GrnList',
        component: GrnList,
        meta: { requiresAuth: true }
    },
    // Production
    {
        path: '/control-room',
        name: 'ControlRoom',
        component: ControlRoom,
        meta: { requiresAuth: true, minRole: 'OPERATOR' }
    },
    // Sales
    {
        path: '/sales',
        name: 'Sales',
        component: Sales,
        meta: { requiresAuth: true }
    },
    {
        path: '/sales/products',
        name: 'Products',
        component: Products,
        meta: { requiresAuth: true }
    },
    {
        path: '/sales/customers',
        name: 'Customers',
        component: Customers,
        meta: { requiresAuth: true }
    },
    {
        path: '/sales/dispatches',
        name: 'Dispatches',
        component: Dispatches,
        meta: { requiresAuth: true }
    },
    {
        path: '/sales/quotations',
        name: 'Quotations',
        component: () => import('./views/sales/Quotations.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/sales/orders',
        name: 'SaleOrders',
        component: () => import('./views/sales/SaleOrders.vue'),
        meta: { requiresAuth: true }
    },
    {
        path: '/sales/returns',
        name: 'SalesReturns',
        component: () => import('./views/sales/SalesReturns.vue'),
        meta: { requiresAuth: true }
    },
    // Maintenance
    {
        path: '/maintenance',
        name: 'MaintenanceHub',
        component: () => import('./views/MaintenanceHub.vue'),
        meta: { requiresAuth: true }
    },
    // Settings
    {
        path: '/settings/recipes',
        name: 'RecipeManager',
        component: RecipeManager,
        meta: { requiresAuth: true, minRole: 'MANAGER' }
    },
    // Reports (Admin/Manager)
    {
        path: '/reports',
        name: 'Reports',
        component: () => import('./views/Reports.vue'),
        meta: { requiresAuth: true, minRole: 'MANAGER' }
    },
    // User Management (Admin only)
    {
        path: '/settings/users',
        name: 'UserManagement',
        component: () => import('./views/settings/UserManagement.vue'),
        meta: { requiresAuth: true, minRole: 'ADMIN' }
    },
]

const router = createRouter({
    history: createWebHistory(),
    routes
})

// Role hierarchy for permission checks
const roleHierarchy = { ADMIN: 4, MANAGER: 3, OPERATOR: 2, VIEWER: 1 }

// Navigation guard
router.beforeEach((to, from, next) => {
    const token = localStorage.getItem('token')
    const user = JSON.parse(localStorage.getItem('user') || '{}')

    // Check if route requires auth
    if (to.meta.requiresAuth !== false) {
        if (!token) {
            return next('/login')
        }

        // Check role requirement
        if (to.meta.minRole) {
            const userLevel = roleHierarchy[user.role] || 0
            const requiredLevel = roleHierarchy[to.meta.minRole] || 999

            if (userLevel < requiredLevel) {
                alert('Access denied. Insufficient permissions.')
                return next(from.path || '/')
            }
        }
    }

    // If already logged in, redirect from login to dashboard
    if (to.path === '/login' && token) {
        return next('/')
    }

    next()
})

export default router
