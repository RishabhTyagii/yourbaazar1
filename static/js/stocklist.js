// Wait for DOM to be fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Stock update functionality
    window.updateStock = function(variantId) {
        const stockInput = document.getElementById(`stock-input-${variantId}`);
        const stockDisplay = document.getElementById(`stock-display-${variantId}`);
        const statusSpan = document.getElementById(`status-${variantId}`);
        
        const newStock = stockInput.value;
        
        // Show loading state
        statusSpan.innerHTML = '<span style="color:#4f46e5"><svg style="width:1rem;height:1rem;animation:spin 1s linear infinite" viewBox="0 0 24 24"><path fill="currentColor" d="M12,4V2A10,10 0 0,0 2,12H4A8,8 0 0,1 12,4Z"/></svg> Updating...</span>';
        
        fetch(`/update-stock/${variantId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': getCookie('csrftoken'),
            },
            body: `stock=${newStock}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                stockDisplay.textContent = data.new_stock;
                statusSpan.innerHTML = '<span style="color:#10b981"><svg style="width:1rem;height:1rem" viewBox="0 0 24 24"><path fill="currentColor" d="M9,20.42L2.79,14.21L5.62,11.38L9,14.77L18.88,4.88L21.71,7.71L9,20.42Z"/></svg> Updated</span>';
                
                // Update stock badge color and icon
                if (data.new_stock == 0) {
                    stockDisplay.style.background = "#fee2e2";
                    stockDisplay.style.color = "#dc2626";
                    stockDisplay.innerHTML = '<svg style="width:1rem;height:1rem;margin-right:0.25rem" viewBox="0 0 24 24"><path fill="currentColor" d="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zm1,15h-2v-2h2v2zm0,-4h-2V7h2v6z"/></svg>' + data.new_stock;
                } else if (data.new_stock < 15) {
                    stockDisplay.style.background = "#fef3c7";
                    stockDisplay.style.color = "#d97706";
                    stockDisplay.innerHTML = '<svg style="width:1rem;height:1rem;margin-right:0.25rem" viewBox="0 0 24 24"><path fill="currentColor" d="M12,2L4,5v6.09c0,5.05 3.41,9.76 8,10.91 4.59,-1.15 8,-5.86 8,-10.91V5l-8,-3zm-1.06,13.54L7.4,12l1.41,-1.41 2.12,2.12 4.24,-4.24 1.41,1.41 -5.64,5.66z"/></svg>' + data.new_stock;
                } else {
                    stockDisplay.style.background = "#d1fae5";
                    stockDisplay.style.color = "#059669";
                    stockDisplay.innerHTML = '<svg style="width:1rem;height:1rem;margin-right:0.25rem" viewBox="0 0 24 24"><path fill="currentColor" d="M9,16.17L4.83,12l-1.42,1.41L9,19 21,7l-1.41,-1.41L9,16.17z"/></svg>' + data.new_stock;
                }
                
                // Update the row's data attribute
                const row = document.querySelector(`tr[data-variant="${variantId}"]`);
                if (row) {
                    row.setAttribute('data-stock', data.new_stock);
                    // Re-apply filters if needed
                    applyCurrentFilter();
                }
            } else {
                statusSpan.innerHTML = '<span style="color:#ef4444"><svg style="width:1rem;height:1rem" viewBox="0 0 24 24"><path fill="currentColor" d="M13,13H11V7H13M13,17H11V15H13M12,2A10,10 0 0,0 2,12A10,10 0 0,0 12,22A10,10 0 0,0 22,12A10,10 0 0,0 12,2Z"/></svg> Error: ' + data.error + '</span>';
            }
        })
        .catch(error => {
            statusSpan.innerHTML = '<span style="color:#ef4444"><svg style="width:1rem;height:1rem" viewBox="0 0 24 24"><path fill="currentColor" d="M12,2C6.48,2 2,6.48 2,12s4.48,10 10,10 10,-4.48 10,-10S17.52,2 12,2zm1,15h-2v-2h2v2zm0,-4h-2V7h2v6z"/></svg> Network Error</span>';
        });
    }

    // Tab filtering functionality
    let currentFilter = 'all';

    function applyCurrentFilter() {
        const rows = document.querySelectorAll('.variant-row');
        
        rows.forEach(row => {
            const stock = parseInt(row.getAttribute('data-stock'));
            
            if (currentFilter === 'all') {
                row.style.display = 'table-row';
            } 
            else if (currentFilter === 'in-stock' && stock >= 15) {
                row.style.display = 'table-row';
            }
            else if (currentFilter === 'low-stock' && stock > 0 && stock < 15) {
                row.style.display = 'table-row';
            }
            else if (currentFilter === 'out-of-stock' && stock === 0) {
                row.style.display = 'table-row';
            }
            else {
                row.style.display = 'none';
            }
        });
    }

    // Helper function to get CSRF token
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

    // Set up tab buttons
    document.querySelectorAll('.tab-button').forEach(btn => {
        btn.addEventListener('click', function() {
            // Update active tab styling
            document.querySelectorAll('.tab-button').forEach(b => {
                b.style.background = '#e5e7eb';
                b.style.color = '#4b5563';
            });
            this.style.background = '#4f46e5';
            this.style.color = 'white';
            
            // Set current filter and apply
            currentFilter = this.getAttribute('data-tab');
            applyCurrentFilter();
            
            // Update URL without reload
            const url = new URL(window.location.href);
            url.searchParams.set('filter', currentFilter);
            window.history.pushState({}, '', url.toString());
        });
    });

    // Live search functionality with debounce
    let searchTimer;
    document.getElementById('stock-search').addEventListener('input', function() {
        clearTimeout(searchTimer);
        searchTimer = setTimeout(() => {
            const searchTerm = this.value.trim();
            const url = new URL(window.location.href);
            
            if (searchTerm.length > 0) {
                url.searchParams.set('q', searchTerm);
            } else {
                url.searchParams.delete('q');
            }
            // Reset to first page when searching
            url.searchParams.set('page', '1');
            
            window.location.href = url.toString();
        }, 500); // 500ms delay
    });

    // Also submit on Enter key
    document.getElementById('stock-search').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') {
            clearTimeout(searchTimer);
            const searchTerm = this.value.trim();
            const url = new URL(window.location.href);
            
            if (searchTerm.length > 0) {
                url.searchParams.set('q', searchTerm);
            } else {
                url.searchParams.delete('q');
            }
            // Reset to first page when searching
            url.searchParams.set('page', '1');
            
            window.location.href = url.toString();
        }
    });

    // Initialize filter from URL
    const urlParams = new URLSearchParams(window.location.search);
    const filterParam = urlParams.get('filter');
    if (filterParam && ['all', 'in-stock', 'low-stock', 'out-of-stock'].includes(filterParam)) {
        currentFilter = filterParam;
        const activeTab = document.querySelector(`.tab-button[data-tab="${filterParam}"]`);
        if (activeTab) {
            activeTab.click(); // This will apply the filter and update styling
        }
    } else {
        applyCurrentFilter(); // Apply default filter
    }

    // Add animation for status cards
    document.querySelectorAll('.status-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.style.transform = 'translateY(-2px)';
            card.style.boxShadow = '0 4px 6px rgba(0,0,0,0.1)';
        });
        card.addEventListener('mouseleave', () => {
            card.style.transform = '';
            card.style.boxShadow = '0 1px 3px rgba(0,0,0,0.1)';
        });
    });
});