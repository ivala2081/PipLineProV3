/**
 * PSP Allocation Auto-Save - Automatically saves allocation changes
 */
(function() {
    'use strict';
    
    // Debounce function to limit API calls
    function debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
    
    // Function to show notification
    function showNotification(message, type) {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `alert alert-${type === 'success' ? 'success' : 'danger'} alert-dismissible fade show position-fixed`;
        notification.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        notification.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto remove after 3 seconds
        setTimeout(() => {
            if (notification.parentNode) {
                notification.remove();
            }
        }, 3000);
    }
    
    // Function to update save indicator
    function updateSaveIndicator(input, status) {
        const indicator = input.parentElement.querySelector('.save-indicator');
        if (!indicator) return;
        
        const successIcon = indicator.querySelector('.bi-check-circle-fill');
        const loadingIcon = indicator.querySelector('.bi-arrow-clockwise');
        
        // Hide all icons first
        successIcon.style.display = 'none';
        loadingIcon.style.display = 'none';
        
        switch (status) {
            case 'loading':
                loadingIcon.style.display = 'inline-block';
                break;
            case 'success':
                successIcon.style.display = 'inline-block';
                break;
            case 'error':
                // Could add error icon here if needed
                break;
        }
    }
    
    // Function to save allocation
    function saveAllocation(input) {
        const date = input.getAttribute('data-date');
        const psp = input.getAttribute('data-psp');
        const value = input.value;
        
        if (!date || !psp) {
            console.error('Missing required attributes for allocation save');
            return;
        }
        
        // Show loading indicator
        updateSaveIndicator(input, 'loading');
        
        // Get CSRF token
        const csrfToken = document.querySelector('meta[name="csrf-token"]')?.getAttribute('content');
        if (!csrfToken) {
            showNotification('CSRF token not found. Please refresh the page.', 'error');
            updateSaveIndicator(input, 'error');
            return;
        }
        
        // Send allocation update
        fetch('/api/psp-allocations', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest',
                'X-CSRFToken': csrfToken
            },
            body: JSON.stringify({
                date: date,
                psp: psp,
                allocation: value
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Show success indicator
                updateSaveIndicator(input, 'success');
                
                // Update rollover calculation
                updateRollover(input);
                
                // Hide success indicator after 2 seconds
                setTimeout(() => {
                    updateSaveIndicator(input, '');
                }, 2000);
            } else {
                throw new Error(data.message || 'Failed to save allocation');
            }
        })
        .catch(error => {
            console.error('Error saving allocation:', error);
            updateSaveIndicator(input, 'error');
            showNotification('Failed to save allocation: ' + error.message, 'error');
        });
    }
    
    // Function to update rollover calculation and status
    function updateRollover(input) {
        const row = input.closest('.psp-row');
        const netAmount = parseFloat(input.getAttribute('data-net') || 0);
        const allocationAmount = parseFloat(input.value || 0);
        const rolloverAmount = netAmount - allocationAmount;
        
        // Update rollover amount display
        const rolloverElement = row.querySelector('.amount-rollover');
        if (rolloverElement) {
            rolloverElement.textContent = rolloverAmount.toLocaleString('tr-TR', {
                minimumFractionDigits: 2,
                maximumFractionDigits: 2
            });
        }
        
        // Update status based on rollover amount
        updateStatusBasedOnRollover(row, rolloverAmount);
    }
    
    // Function to update status based on rollover amount
    function updateStatusBasedOnRollover(row, rolloverAmount) {
        const statusCell = row.querySelector('.status-cell');
        if (!statusCell) return;
        
        // Remove existing status badge
        const existingBadge = statusCell.querySelector('.status-badge');
        if (existingBadge) {
            existingBadge.remove();
        }
        
        // Create new status badge based on rollover amount
        let statusText, statusClass;
        
        if (rolloverAmount <= 0) {
            // PSP owes company money (positive for company)
            statusText = 'PSP Owes You';
            statusClass = 'status-paid';
        } else if (rolloverAmount < parseFloat(row.querySelector('.amount-net')?.textContent.replace(/[^\d.-]/g, '') || 0) * 0.1) {
            // Company owes PSP small amount
            statusText = 'Small Debt';
            statusClass = 'status-almost-paid';
        } else {
            // Company owes PSP significant amount
            statusText = 'You Owe PSP';
            statusClass = 'status-unpaid';
        }
        
        // Create and add new status badge
        const newBadge = document.createElement('span');
        newBadge.className = `status-badge ${statusClass}`;
        newBadge.textContent = statusText;
        statusCell.appendChild(newBadge);
    }
    
    // Debounced save function
    const debouncedSave = debounce(saveAllocation, 1000); // 1 second delay
    
    // Initialize when DOM is loaded
    document.addEventListener('DOMContentLoaded', function() {
        // Find all allocation inputs
        const inputs = document.querySelectorAll('.allocation-field');
        
        inputs.forEach(input => {
            // Add input event listener for real-time calculation and auto-save
            input.addEventListener('input', function() {
                // Update rollover calculation immediately
                updateRollover(this);
                
                // Auto-save with debounce
                debouncedSave(this);
            });
            
            // Add focus event listener to show current value
            input.addEventListener('focus', function() {
                // Could add visual feedback here if needed
            });
            
            // Add blur event listener for immediate save if not already saved
            input.addEventListener('blur', function() {
                // Force save on blur
                saveAllocation(this);
            });
        });
        
        // Initialize rollover calculations and status for all rows
        document.querySelectorAll('.psp-row').forEach(row => {
            const input = row.querySelector('.allocation-field');
            if (input) {
                updateRollover(input);
            }
        });
    });
    
    // Also run initialization after window load to catch any late elements
    window.addEventListener('load', function() {
        // Re-initialize in case elements were added dynamically
        const inputs = document.querySelectorAll('.allocation-field');
        
        inputs.forEach(input => {
            // Only add listeners if not already added
            if (!input.hasAttribute('data-initialized')) {
                input.setAttribute('data-initialized', 'true');
                
                // Add input event listener for real-time calculation and auto-save
                input.addEventListener('input', function() {
                    updateRollover(this);
                    debouncedSave(this);
                });
                
                // Add blur event listener for immediate save
                input.addEventListener('blur', function() {
                    saveAllocation(this);
                });
                
                // Initialize rollover and status
                updateRollover(input);
            }
        });
    });
})(); 