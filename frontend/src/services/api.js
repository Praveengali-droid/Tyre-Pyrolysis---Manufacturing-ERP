import axios from 'axios'

// Use environment variable for API base URL, fallback to localhost for development
const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1'

const api = axios.create({
    baseURL: API_BASE,
    headers: {
        'Content-Type': 'application/json'
    }
})

// Add auth token to requests
api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers.Authorization = `Bearer ${token}`
    }
    return config
})

// Handle 401 Unauthorized responses
api.interceptors.response.use(
    (response) => response,
    (error) => {
        if (error.response?.status === 401) {
            localStorage.removeItem('token')
            localStorage.removeItem('user')
            window.location.href = '/login'
        }
        return Promise.reject(error)
    }
)

// Auth API
export const authApi = {
    login: (username, password) => api.post('/auth/login', { username, password }),
    me: () => api.get('/auth/me'),
    logout: () => {
        localStorage.removeItem('token')
        localStorage.removeItem('user')
        window.location.href = '/login'
    },
    // User management (Admin only)
    listUsers: () => api.get('/auth/users'),
    createUser: (data) => api.post('/auth/users', data),
    resetPassword: (userId, newPassword) => api.put(`/auth/users/${userId}/reset-password`, { new_password: newPassword }),
    deactivateUser: (userId) => api.put(`/auth/users/${userId}/deactivate`),
    activateUser: (userId) => api.put(`/auth/users/${userId}/activate`),
    // Audit logs
    getAuditLogs: (entityType = null, action = null) => api.get('/auth/audit-logs', { params: { entity_type: entityType, action } })
}

// Vendor API
export const vendorApi = {
    list: (params = {}) => api.get('/procurement/vendors', { params }),
    get: (id) => api.get(`/procurement/vendors/${id}`),
    create: (data) => api.post('/procurement/vendors', data),
    update: (id, data) => api.put(`/procurement/vendors/${id}`, data),
    delete: (id) => api.delete(`/procurement/vendors/${id}`)
}

// Raw Material API
export const rawMaterialApi = {
    list: () => api.get('/procurement/raw-materials'),
    create: (data) => api.post('/procurement/raw-materials', data)
}

// Purchase Order API
export const purchaseOrderApi = {
    list: (params = {}) => api.get('/procurement/purchase-orders', { params }),
    listOpen: () => api.get('/procurement/purchase-orders/open'),
    get: (id) => api.get(`/procurement/purchase-orders/${id}`),
    create: (data) => api.post('/procurement/purchase-orders', data),
    confirm: (id) => api.put(`/procurement/purchase-orders/${id}/confirm`)
}

// Inward Entry / GRN API
export const inwardApi = {
    getStats: () => api.get('/procurement/stats'),
    calculate: (data) => api.post('/procurement/inward-entry/calculate', data),
    create: (data) => api.post('/procurement/inward-entry', data),
    listGrns: (params = {}) => api.get('/procurement/grn', { params }),
    getGrn: (id) => api.get(`/procurement/grn/${id}`),
    approveGrn: (id, approvedBy) => api.put(`/procurement/grn/${id}/approve`, null, { params: { approved_by: approvedBy } })
}

// Production API
export const productionApi = {
    // Reactors
    listReactors: () => api.get('/production/reactors'),
    createReactor: (code, name, capacity) => api.post('/production/reactors', null, {
        params: { reactor_code: code, name, capacity_kg: capacity }
    }),
    updateReactorStatus: (id, status) => api.put(`/production/reactors/${id}/status`, null, {
        params: { new_status: status }
    }),

    // Lots (FIFO)
    listAvailableLots: () => api.get('/production/lots/available'),

    // Batches
    listBatches: (params = {}) => api.get('/production/batches', { params }),
    getBatch: (id) => api.get(`/production/batches/${id}`),
    startBatch: (data) => api.post('/production/batches/start', data),
    completeBatch: (id, data) => api.post(`/production/batches/${id}/complete`, data),

    // Batch Hold/Resume
    holdBatch: (id, reason = 'Maintenance') => api.put(`/production/batches/${id}/hold`, null, { params: { reason } }),
    resumeBatch: (id) => api.put(`/production/batches/${id}/resume`),
    advanceStage: (id) => api.put(`/production/batches/${id}/advance-stage`),

    // Timeline (for progress tracking)
    getBatchTimeline: (id) => api.get(`/production/batches/${id}/timeline`),

    // Production Summary (for dashboard)
    getSummary: () => api.get('/production/summary'),

    // Log Entries
    addLogEntry: (batchId, data) => api.post(`/production/batches/${batchId}/log-entry`, data),
    getBatchLogs: (batchId) => api.get(`/production/batches/${batchId}/logs`),

    // Recipes
    listRecipes: () => api.get('/production/recipes'),
    getRecipe: (id) => api.get(`/production/recipes/${id}`),
    createRecipe: (data) => api.post('/production/recipes', data),
}

// Tank Farm API
export const tankFarmApi = {
    listTanks: () => api.get('/tank-farm/tanks'),
    createTank: (data) => api.post('/tank-farm/tanks', data),
    getTank: (id) => api.get(`/tank-farm/tanks/${id}`),
    listTransfers: () => api.get('/tank-farm/transfers'),
    createTransfer: (data) => api.post('/tank-farm/transfers', data)
}

// Sales API
export const salesApi = {
    // Products
    listProducts: () => api.get('/sales/products'),
    createProduct: (data) => api.post('/sales/products', data),
    getProduct: (id) => api.get(`/sales/products/${id}`),

    // Customers
    listCustomers: () => api.get('/sales/customers'),
    createCustomer: (data) => api.post('/sales/customers', data),
    getCustomer: (id) => api.get(`/sales/customers/${id}`),
    getCustomerLedger: (id) => api.get(`/sales/customers/${id}/ledger`),

    // Carbon Dispatch
    listCarbonDispatches: () => api.get('/sales/carbon/dispatches'),
    createCarbonDispatch: (data) => api.post('/sales/carbon/dispatch', data),
    confirmCarbonReceipt: (id) => api.put(`/sales/carbon/dispatches/${id}/confirm`),

    // Steel Dispatch
    listSteelDispatches: () => api.get('/sales/steel/dispatches'),
    createSteelDispatch: (data) => api.post('/sales/steel/dispatch', data),
    confirmSteelReceipt: (id) => api.put(`/sales/steel/dispatches/${id}/confirm`),

    // Summary
    getSummary: () => api.get('/sales/summary')
}

// Quotation API
export const quotationApi = {
    // Quotations
    list: (status = null) => api.get('/quotations/', { params: { status } }),
    get: (id) => api.get(`/quotations/${id}`),
    getItems: (id) => api.get(`/quotations/${id}/items`),
    create: (data) => api.post('/quotations/', data),
    send: (id) => api.put(`/quotations/${id}/send`),
    accept: (id) => api.put(`/quotations/${id}/accept`),
    reject: (id) => api.put(`/quotations/${id}/reject`),
    convert: (id) => api.post(`/quotations/${id}/convert`),
    getSummary: () => api.get('/quotations/summary'),

    // Sale Orders
    listOrders: (status = null) => api.get('/quotations/orders/list', { params: { status } }),
    getOrder: (id) => api.get(`/quotations/orders/${id}`)
}

// Dispatch API
export const dispatchApi = {
    // Dispatches
    list: (saleOrderId = null, status = null) => api.get('/dispatches/', { params: { sale_order_id: saleOrderId, status } }),
    get: (id) => api.get(`/dispatches/${id}`),
    getItems: (id) => api.get(`/dispatches/${id}/items`),
    create: (data) => api.post('/dispatches/', data),
    ship: (id) => api.put(`/dispatches/${id}/ship`),
    deliver: (id) => api.put(`/dispatches/${id}/deliver`),

    // Invoice
    generateInvoice: (id) => api.post(`/dispatches/${id}/generate-invoice`),
    getInvoice: (id) => api.get(`/dispatches/${id}/invoice`),

    // Documents
    getDeliveryChallan: (id) => api.get(`/dispatches/${id}/documents/dc`),
    getGatePass: (id) => api.get(`/dispatches/${id}/documents/gatepass`),
    getInvoiceDocument: (id) => api.get(`/dispatches/${id}/documents/invoice`),

    // SO helpers
    getPendingItems: (orderId) => api.get(`/dispatches/orders/${orderId}/pending-items`)
}

// Returns API
export const returnsApi = {
    // Returns
    list: (status = null) => api.get('/returns/', { params: { status } }),
    get: (id) => api.get(`/returns/${id}`),
    getItems: (id) => api.get(`/returns/${id}/items`),
    create: (data) => api.post('/returns/', data),
    receive: (id) => api.put(`/returns/${id}/receive`),
    qcPass: (id, notes = null) => api.put(`/returns/${id}/qc-pass`, null, { params: { qc_notes: notes } }),
    qcFail: (id, notes = null) => api.put(`/returns/${id}/qc-fail`, null, { params: { qc_notes: notes } }),

    // QC Dashboard
    getPendingQC: () => api.get('/returns/pending-qc'),

    // Credit Note
    getCreditNote: (id) => api.get(`/returns/${id}/credit-note`),
    getCreditNoteDocument: (id) => api.get(`/returns/${id}/credit-note/document`),

    // Invoice returnable items
    getReturnableItems: (invoiceId) => api.get(`/returns/invoices/${invoiceId}/returnable-items`)
}

// Maintenance API
export const maintenanceApi = {
    // Schedules
    listSchedules: (reactorId = null) => api.get('/maintenance/schedules', { params: { reactor_id: reactorId } }),
    createSchedule: (data) => api.post('/maintenance/schedules', data),

    // Due Tasks Dashboard
    getDueTasks: () => api.get('/maintenance/due-tasks'),
    getReactorStatus: () => api.get('/maintenance/reactor-status'),

    // Complete Task (with optional photo upload)
    completeTask: (formData) => api.post('/maintenance/complete-task', formData, {
        headers: { 'Content-Type': 'multipart/form-data' }
    }),

    // Logs
    listLogs: (reactorId = null, limit = 50) => api.get('/maintenance/logs', { params: { reactor_id: reactorId, limit } }),

    // Safety interlock check
    checkInterlock: (reactorId) => api.get(`/maintenance/check-interlock/${reactorId}`),

    // Maintenance Requests
    listRequests: (status = null, priority = null) => api.get('/maintenance/requests', { params: { status_filter: status, priority } }),
    getRequestsSummary: () => api.get('/maintenance/requests/summary'),
    getRequest: (id) => api.get(`/maintenance/requests/${id}`),
    createRequest: (data) => api.post('/maintenance/requests', data),
    assignRequest: (id, assignedTo) => api.put(`/maintenance/requests/${id}/assign`, null, { params: { assigned_to: assignedTo } }),
    updateRequestStatus: (id, newStatus) => api.put(`/maintenance/requests/${id}/status`, null, { params: { new_status: newStatus } }),
    completeRequest: (id, data) => api.put(`/maintenance/requests/${id}/complete`, null, { params: data }),

    // Spare Parts
    listSpareParts: (category = null) => api.get('/maintenance/spare-parts', { params: { category } }),
    getSparePartsSummary: () => api.get('/maintenance/spare-parts/summary'),
    getLowStockParts: () => api.get('/maintenance/spare-parts/low-stock'),
    createSparePart: (data) => api.post('/maintenance/spare-parts', data),
    receiveStock: (partId, quantity, unitPrice = null, location = null) => api.post(`/maintenance/spare-parts/${partId}/receive`, null, { params: { quantity, unit_price: unitPrice, location } }),
    issueStock: (partId, quantity, requestId = null, issuedBy = 'Technician', notes = null) => api.post(`/maintenance/spare-parts/${partId}/issue`, null, { params: { quantity, request_id: requestId, issued_by: issuedBy, notes } })
}

// Reports API
export const reportsApi = {
    // System Settings
    getSettings: () => api.get('/reports/settings'),
    updateSetting: (key, value) => api.put(`/reports/settings/${key}`, null, { params: { value } }),

    // Reports with time filters
    getVendorYield: (period = 'this_month', startDate = null, endDate = null) =>
        api.get('/reports/vendor-yield', { params: { period, start_date: startDate, end_date: endDate } }),

    getInventoryValuation: () => api.get('/reports/inventory-valuation'),

    getDowntimeAnalysis: (period = 'this_month', startDate = null, endDate = null) =>
        api.get('/reports/downtime-analysis', { params: { period, start_date: startDate, end_date: endDate } }),

    getProfitability: (period = 'this_month', startDate = null, endDate = null) =>
        api.get('/reports/profitability', { params: { period, start_date: startDate, end_date: endDate } }),

    getProductionSummary: (period = 'this_month', startDate = null, endDate = null) =>
        api.get('/reports/production-summary', { params: { period, start_date: startDate, end_date: endDate } }),

    getSalesPerformance: (period = 'this_month', startDate = null, endDate = null) =>
        api.get('/reports/sales-performance', { params: { period, start_date: startDate, end_date: endDate } }),

    // CSV Exports
    exportVendorYieldCSV: (period = 'this_month') =>
        api.get('/reports/vendor-yield', { params: { period, export_csv: true }, responseType: 'blob' }),

    exportDowntimeCSV: (period = 'this_month') =>
        api.get('/reports/downtime-analysis', { params: { period, export_csv: true }, responseType: 'blob' }),

    exportSalesCSV: (period = 'this_month') =>
        api.get('/reports/sales-performance', { params: { period, export_csv: true }, responseType: 'blob' })
}

// Dashboard API
export const dashboardApi = {
    getSummary: () => api.get('/dashboard/summary'),
    getAlerts: () => api.get('/dashboard/alerts'),
    getActivity: (limit = 15) => api.get('/dashboard/activity', { params: { limit } })
}

export default api



