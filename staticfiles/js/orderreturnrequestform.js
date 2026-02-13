// Function to handle image previews
function setupImagePreviews() {
    const setupPreview = (inputId, previewId) => {
        const input = document.getElementById(inputId);
        const preview = document.getElementById(previewId);
        
        if (input && preview) {
            input.addEventListener('change', function() {
                if (this.files && this.files[0]) {
                    const reader = new FileReader();
                    reader.onload = function(e) {
                        preview.src = e.target.result;
                        preview.style.display = 'block';
                    };
                    reader.readAsDataURL(this.files[0]);
                }
            });
        }
    };

    setupPreview('id_image1', 'preview_1');
    setupPreview('id_image2', 'preview_2');
    setupPreview('id_image3', 'preview_3');
    setupPreview('id_image4', 'preview_4');
}

// Function to handle order item loading
function setupOrderItemLoading() {
    const orderSelect = document.querySelector('#id_order');
    const orderItemSection = document.querySelector('#order-item-options');

    if (orderSelect && orderItemSection) {
        orderSelect.addEventListener('change', function() {
            const orderId = this.value;
            orderItemSection.innerHTML = '<div class="loading">Loading items...</div>';

            if (orderId) {
                fetch(`/order/ajax/order-items/?order_id=${orderId}`)
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        if (data.items && data.items.length > 0) {
                            orderItemSection.innerHTML = '';
                            data.items.forEach(item => {
                                const div = document.createElement('div');
                                div.classList.add('radio-option');
                                div.innerHTML = `
                                    <input type="radio" name="order_item" value="${item.id}" id="item_${item.id}" required>
                                    <label for="item_${item.id}">${item.label}</label>
                                `;
                                orderItemSection.appendChild(div);
                            });
                        } else {
                            orderItemSection.innerHTML = '<div class="no-items">No delivered items available for return.</div>';
                        }
                    })
                    .catch(err => {
                        console.error('Error fetching order items:', err);
                        orderItemSection.innerHTML = '<div class="error">Error loading items. Please try again.</div>';
                    });
            } else {
                orderItemSection.innerHTML = '';
            }
        });

        // Trigger change event if order is already selected
        if (orderSelect.value) {
            orderSelect.dispatchEvent(new Event('change'));
        }
    }
}

// Initialize everything when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    setupImagePreviews();
    setupOrderItemLoading();
    
    // Add any additional initialization here
});