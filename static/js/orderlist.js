document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchInput = document.getElementById('orderSearch');
    const orderRows = document.querySelectorAll('.order-row');
    
    searchInput.addEventListener('input', function() {
        const searchTerm = this.value.toLowerCase();
        
        orderRows.forEach(row => {
            const orderNumber = row.getAttribute('data-number');
            const trackingId = row.getAttribute('data-tracking');
            const orderId = row.getAttribute('data-id').toString();
            
            if (orderNumber.includes(searchTerm) || 
                trackingId.includes(searchTerm) || 
                orderId.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    });
    
    // Status filter functionality
    const statusFilterBtns = document.querySelectorAll('.status-filter-btn');
    
    statusFilterBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            // Remove active class from all buttons
            statusFilterBtns.forEach(b => b.classList.remove('active'));
            
            // Add active class to clicked button
            this.classList.add('active');
            
            const status = this.textContent.toLowerCase().replace(' ', '-');
            
            orderRows.forEach(row => {
                if (status === 'all-orders') {
                    row.style.display = '';
                } else {
                    const rowStatus = row.getAttribute('data-status');
                    
                    if (rowStatus === status) {
                        row.style.display = '';
                    } else {
                        row.style.display = 'none';
                    }
                }
            });
        });
    });
});