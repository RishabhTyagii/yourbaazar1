   // Enhanced Price Sorting
    document.getElementById('sortBy').addEventListener('change', function() {
        const sortValue = this.value;
        const productGrid = document.querySelector('.product-grid');
        const productCards = Array.from(document.querySelectorAll('.product-card'));
        
        // Sort products
        switch(sortValue) {
            case 'price-asc':
                productCards.sort((a, b) => 
                    parseFloat(a.dataset.price) - parseFloat(b.dataset.price));
                break;
            case 'price-desc':
                productCards.sort((a, b) => 
                    parseFloat(b.dataset.price) - parseFloat(a.dataset.price));
                break;
            case 'newest':
                productCards.sort((a, b) => 
                    new Date(b.dataset.date) - new Date(a.dataset.date));
                break;
            default:
                // Default sorting (original order)
                productCards.sort((a, b) => 
                    Array.from(productGrid.children).indexOf(a) - Array.from(productGrid.children).indexOf(b));
        }
        
        // Re-append sorted products with animation
        productCards.forEach((card, index) => {
            card.style.opacity = '0';
            card.style.transform = 'translateY(10px)';
            card.style.transition = 'all 0.3s ease';
            
            setTimeout(() => {
                productGrid.appendChild(card);
                
                setTimeout(() => {
                    card.style.opacity = '1';
                    card.style.transform = 'translateY(0)';
                }, 50 * index);
            }, 0);
        });
    });