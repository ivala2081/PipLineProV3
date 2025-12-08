/* ===== UNIFIED TAB SYSTEM - BASED ON CLIENTS PAGE ===== */
/* Version: 1.0.0 | Standardized: 2025-08-06 | Source: Clients Page Tab System */

// Tab persistence functionality
document.addEventListener('DOMContentLoaded', function() {
    // Get current tab from URL or default to first tab
    const urlParams = new URLSearchParams(window.location.search);
    const currentTab = urlParams.get('tab') || getDefaultTab();
    
    // Show the correct tab on page load
    const targetTab = document.querySelector(`#${currentTab}-tab`);
    const targetContent = document.querySelector(`#${currentTab}`);
    
    if (targetTab && targetContent) {
        // Remove active class from all tabs and content
        document.querySelectorAll('.nav-link').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-pane').forEach(content => {
            content.classList.remove('show', 'active');
        });
        
        // Add active class to current tab and content
        targetTab.classList.add('active');
        targetContent.classList.add('show', 'active');
    }
    
    // Handle tab clicks to update URL
    document.querySelectorAll('.nav-link').forEach(tab => {
        tab.addEventListener('click', function(e) {
            const tabId = this.id.replace('-tab', '');
            const url = new URL(window.location);
            url.searchParams.set('tab', tabId);
            window.history.pushState({}, '', url);
        });
    });
    
    // Ensure tab state is preserved on form submissions
    // Update all forms to preserve the current tab
    document.querySelectorAll('form').forEach(form => {
        const action = form.getAttribute('action');
        if (action) {
            // Update form action to include current tab
            const url = new URL(action, window.location.origin);
            url.searchParams.set('tab', currentTab);
            form.setAttribute('action', url.toString());
        }
        
        // Add hidden input for tab if not already present
        if (!form.querySelector('input[name="tab"]')) {
            const tabInput = document.createElement('input');
            tabInput.type = 'hidden';
            tabInput.name = 'tab';
            tabInput.value = currentTab;
            form.appendChild(tabInput);
        }
    });
});

// Helper function to get default tab based on page
function getDefaultTab() {
    const path = window.location.pathname;
    
    // Define default tabs for different pages
    const defaultTabs = {
        '/clients': 'overview',
        '/analytics': 'dashboard',
        '/transactions': 'list',
        '/psp-track': 'overview',
        '/settings': 'profile',
        '/agent-management': 'overview',
        '/business-analytics': 'overview'
    };
    
    // Find matching path
    for (const [pagePath, defaultTab] of Object.entries(defaultTabs)) {
        if (path.includes(pagePath.replace('/', ''))) {
            return defaultTab;
        }
    }
    
    // Fallback to first available tab
    const firstTab = document.querySelector('.nav-link');
    if (firstTab) {
        return firstTab.id.replace('-tab', '');
    }
    
    return 'overview';
}

// Enhanced tab switching with smooth transitions
function switchTab(tabId) {
    // Remove active class from all tabs and content
    document.querySelectorAll('.nav-link').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-pane').forEach(content => {
        content.classList.remove('show', 'active');
    });
    
    // Add active class to target tab and content
    const targetTab = document.querySelector(`#${tabId}-tab`);
    const targetContent = document.querySelector(`#${tabId}`);
    
    if (targetTab && targetContent) {
        targetTab.classList.add('active');
        targetContent.classList.add('show', 'active');
        
        // Update URL
        const url = new URL(window.location);
        url.searchParams.set('tab', tabId);
        window.history.pushState({}, '', url);
        
        // Trigger custom event for tab change
        const event = new CustomEvent('tabChanged', {
            detail: { tabId: tabId }
        });
        document.dispatchEvent(event);
    }
}

// Export for global use
window.switchTab = switchTab;
