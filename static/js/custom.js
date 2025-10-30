// Custom JavaScript for Ligisoo Tips Marketplace

// Configure HTMX
htmx.config.globalViewTransitions = true;
htmx.config.defaultSwapStyle = 'innerHTML';
htmx.config.defaultSwapDelay = 100;

// Add fade-in class to swapped content
document.body.addEventListener('htmx:afterSwap', function(event) {
    event.detail.target.classList.add('fade-in');
});

// Show loading state
document.body.addEventListener('htmx:beforeRequest', function(event) {
    event.detail.elt.classList.add('htmx-request');
});

document.body.addEventListener('htmx:afterRequest', function(event) {
    event.detail.elt.classList.remove('htmx-request');
});

// Utility function to get CSRF token
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Toast notification system
function showToast(message, type = 'info', duration = 3000) {
    const toast = document.createElement('div');
    const typeClasses = {
        'success': 'bg-green-600 text-white',
        'error': 'bg-red-600 text-white',
        'warning': 'bg-yellow-600 text-white',
        'info': 'bg-blue-600 text-white'
    };

    toast.className = `fixed top-4 right-4 z-50 p-4 rounded-md shadow-lg ${typeClasses[type] || typeClasses.info}`;
    toast.textContent = message;

    document.body.appendChild(toast);

    setTimeout(() => {
        toast.style.transition = 'opacity 0.3s';
        toast.style.opacity = '0';
        setTimeout(() => {
            if (document.body.contains(toast)) {
                document.body.removeChild(toast);
            }
        }, 300);
    }, duration);
}

// Make functions globally available
window.getCookie = getCookie;
window.showToast = showToast;

console.log('Ligisoo custom.js loaded successfully');
