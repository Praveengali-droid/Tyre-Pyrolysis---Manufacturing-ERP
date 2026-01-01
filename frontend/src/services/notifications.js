/**
 * Notification Service - Handles toast notifications with optional sound
 */

// Notification queue
const notifications = []
let notificationId = 0

// Sound effects
const sounds = {
    alert: '/sounds/alert.mp3',
    success: '/sounds/success.mp3',
    warning: '/sounds/warning.mp3'
}

// Create notification element if not exists
function ensureContainer() {
    let container = document.getElementById('notification-container')
    if (!container) {
        container = document.createElement('div')
        container.id = 'notification-container'
        container.className = 'fixed top-4 right-4 z-50 space-y-2 max-w-sm'
        document.body.appendChild(container)
    }
    return container
}

// Play sound
function playSound(type = 'alert') {
    try {
        const audio = new Audio(sounds[type] || sounds.alert)
        audio.volume = 0.5
        audio.play().catch(() => { }) // Ignore autoplay restrictions
    } catch (e) {
        console.log('Sound not available')
    }
}

// Show notification
export function notify(message, options = {}) {
    const {
        type = 'info', // info, success, warning, error
        duration = 5000,
        sound = false,
        title = null
    } = options

    const id = ++notificationId
    const container = ensureContainer()

    // Type styles
    const typeStyles = {
        info: 'bg-blue-600 text-white',
        success: 'bg-green-600 text-white',
        warning: 'bg-yellow-500 text-yellow-900',
        error: 'bg-red-600 text-white'
    }

    const icons = {
        info: 'ℹ️',
        success: '✓',
        warning: '⚠️',
        error: '✕'
    }

    // Create notification element
    const el = document.createElement('div')
    el.id = `notification-${id}`
    el.className = `${typeStyles[type]} px-4 py-3 rounded-lg shadow-lg flex items-start space-x-3 transform transition-all duration-300 translate-x-full opacity-0`
    el.innerHTML = `
    <span class="text-lg">${icons[type]}</span>
    <div class="flex-1">
      ${title ? `<p class="font-bold text-sm">${title}</p>` : ''}
      <p class="text-sm">${message}</p>
    </div>
    <button onclick="this.parentElement.remove()" class="text-white/80 hover:text-white">✕</button>
  `

    container.appendChild(el)

    // Animate in
    requestAnimationFrame(() => {
        el.classList.remove('translate-x-full', 'opacity-0')
    })

    // Play sound if requested
    if (sound) {
        playSound(type === 'error' ? 'warning' : type === 'success' ? 'success' : 'alert')
    }

    // Auto remove
    if (duration > 0) {
        setTimeout(() => {
            el.classList.add('translate-x-full', 'opacity-0')
            setTimeout(() => el.remove(), 300)
        }, duration)
    }

    return id
}

// Convenience methods
export const notifySuccess = (msg, opts = {}) => notify(msg, { ...opts, type: 'success' })
export const notifyWarning = (msg, opts = {}) => notify(msg, { ...opts, type: 'warning' })
export const notifyError = (msg, opts = {}) => notify(msg, { ...opts, type: 'error' })
export const notifyInfo = (msg, opts = {}) => notify(msg, { ...opts, type: 'info' })

// Batch-specific alerts
export function alertBatchNearlyDone(batchNumber, minsRemaining) {
    notify(`Batch ${batchNumber} completing in ~${minsRemaining} minutes!`, {
        type: 'warning',
        title: '⏰ Batch Nearly Done',
        sound: true,
        duration: 10000
    })
}

export function alertStageComplete(batchNumber, stageName) {
    notify(`${stageName} stage complete. Review readings and advance to next stage.`, {
        type: 'info',
        title: `📋 ${batchNumber}`,
        sound: true,
        duration: 8000
    })
}

export function alertTankLevel(tankCode, level, isHigh) {
    const msg = isHigh
        ? `Tank ${tankCode} is ${level.toFixed(0)}% full - near capacity!`
        : `Tank ${tankCode} is only ${level.toFixed(0)}% - low level alert`

    notify(msg, {
        type: isHigh ? 'error' : 'warning',
        title: '🛢️ Tank Alert',
        sound: true,
        duration: 10000
    })
}

export default {
    notify,
    notifySuccess,
    notifyWarning,
    notifyError,
    notifyInfo,
    alertBatchNearlyDone,
    alertStageComplete,
    alertTankLevel
}
