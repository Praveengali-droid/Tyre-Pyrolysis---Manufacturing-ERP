import { ref, onMounted, onUnmounted } from 'vue'
import { productionApi, tankFarmApi } from '../services/api'
import notifications from '../services/notifications'

/**
 * Composable for polling batch and tank status with alerts
 */
export function useProductionAlerts(options = {}) {
    const {
        pollIntervalMs = 60000,  // Poll every 60 seconds
        enableBatchAlerts = true,
        enableTankAlerts = true,
        nearlyDoneThresholdMins = 15
    } = options

    const isPolling = ref(false)
    const lastPollTime = ref(null)
    const activeBatches = ref([])
    const tankAlerts = ref([])

    // Track already-alerted items to avoid duplicate notifications
    const alertedBatches = new Set()
    const alertedTanks = new Set()

    let pollInterval = null

    async function checkBatches() {
        if (!enableBatchAlerts) return

        try {
            const response = await productionApi.listBatches({ status: 'IN_PROGRESS,LOADING,ON_HOLD' })
            activeBatches.value = response.data || []

            for (const batch of activeBatches.value) {
                // Skip if already alerted for this batch's current state
                const alertKey = `${batch.id}-${batch.current_stage}`

                // Check for nearly-done batches
                if (batch.expected_end_time) {
                    const endTime = new Date(batch.expected_end_time)
                    const now = new Date()
                    const minsRemaining = Math.max(0, (endTime - now) / 60000)

                    if (minsRemaining <= nearlyDoneThresholdMins && minsRemaining > 0) {
                        const nearlyDoneKey = `${batch.id}-nearly-done`
                        if (!alertedBatches.has(nearlyDoneKey)) {
                            notifications.alertBatchNearlyDone(batch.batch_number, Math.round(minsRemaining))
                            alertedBatches.add(nearlyDoneKey)
                        }
                    }
                }
            }
        } catch (e) {
            console.error('Batch polling error:', e)
        }
    }

    async function checkTanks() {
        if (!enableTankAlerts) return

        try {
            const response = await tankFarmApi.listTanks()
            const tanks = response.data || []

            for (const tank of tanks) {
                const level = tank.fill_percentage || 0

                // High level alert (>90%)
                if (level >= 90) {
                    const alertKey = `${tank.id}-high`
                    if (!alertedTanks.has(alertKey)) {
                        notifications.alertTankLevel(tank.tank_code, level, true)
                        alertedTanks.add(alertKey)
                    }
                }
                // Low level alert (<10%)
                else if (level <= 10 && level > 0) {
                    const alertKey = `${tank.id}-low`
                    if (!alertedTanks.has(alertKey)) {
                        notifications.alertTankLevel(tank.tank_code, level, false)
                        alertedTanks.add(alertKey)
                    }
                }
                // Clear alerts if level is normal
                else {
                    alertedTanks.delete(`${tank.id}-high`)
                    alertedTanks.delete(`${tank.id}-low`)
                }
            }
        } catch (e) {
            console.error('Tank polling error:', e)
        }
    }

    async function poll() {
        lastPollTime.value = new Date()
        await Promise.all([checkBatches(), checkTanks()])
    }

    function startPolling() {
        if (isPolling.value) return
        isPolling.value = true
        poll() // Initial poll
        pollInterval = setInterval(poll, pollIntervalMs)
    }

    function stopPolling() {
        isPolling.value = false
        if (pollInterval) {
            clearInterval(pollInterval)
            pollInterval = null
        }
    }

    // Auto start/stop on mount/unmount
    onMounted(() => {
        startPolling()
    })

    onUnmounted(() => {
        stopPolling()
    })

    return {
        isPolling,
        lastPollTime,
        activeBatches,
        tankAlerts,
        startPolling,
        stopPolling,
        poll
    }
}

export default useProductionAlerts
