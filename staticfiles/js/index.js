// Enhanced Shoes Tab Functionality
document.addEventListener('DOMContentLoaded', function() {
    const tabs = document.querySelectorAll('.shoes-tab');
    const shoeCards = document.querySelectorAll('.shoe-card');
    
    // Filter shoes based on category
    function filterShoes(category) {
        shoeCards.forEach(card => {
            if (category === 'all' || card.dataset.category === category) {
                card.style.display = 'block';
                // Add animation
                card.style.animation = 'fadeIn 0.5s ease forwards';
            } else {
                card.style.display = 'none';
            }
        });
    }
    
    // Tab click event
    tabs.forEach(tab => {
        tab.addEventListener('click', function() {
            // Remove active class from all tabs
            tabs.forEach(t => t.classList.remove('active'));
            // Add active class to clicked tab
            this.classList.add('active');
            
            // Filter shoes
            const category = this.dataset.category;
            filterShoes(category);
        });
    });
    
    // Initialize - show all shoes by default
    filterShoes('all');
});

// Recent Products Carousel Navigation
document.addEventListener('DOMContentLoaded', function() {
    const carousel = document.querySelector('.recent-carousel');
    const prevBtn = document.querySelector('.carousel-prev');
    const nextBtn = document.querySelector('.carousel-next');
    
    if (carousel && prevBtn && nextBtn) {
        const itemWidth = document.querySelector('.recent-item').offsetWidth;
        const gap = 28; // 1.75rem in pixels
        
        prevBtn.addEventListener('click', () => {
            carousel.scrollBy({ left: -itemWidth - gap, behavior: 'smooth' });
        });
        
        nextBtn.addEventListener('click', () => {
            carousel.scrollBy({ left: itemWidth + gap, behavior: 'smooth' });
        });
    }
});

// Back to Top Button
document.addEventListener('DOMContentLoaded', function() {
    const backToTop = document.querySelector('.back-to-top');
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    });

    backToTop.addEventListener('click', function(e) {
        e.preventDefault();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
});

// Initialize animations
document.addEventListener('DOMContentLoaded', function() {
    // Animate elements on scroll
    const animateOnScroll = function() {
        const elements = document.querySelectorAll('.category-card, .product-card, .feature-card, .shoe-card');
        
        elements.forEach(element => {
            const elementPosition = element.getBoundingClientRect().top;
            const screenPosition = window.innerHeight / 1.2;
            
            if (elementPosition < screenPosition) {
                element.style.animation = 'fadeIn 0.6s ease forwards';
            }
        });
    };

    window.addEventListener('scroll', animateOnScroll);
    animateOnScroll(); // Run once on page load
});

// Add hover effect for touch devices
document.addEventListener('DOMContentLoaded', function() {
    if ('ontouchstart' in window) {
        document.querySelectorAll('.shoe-card, .product-card').forEach(card => {
            card.addEventListener('touchstart', function() {
                this.classList.add('hover-effect');
            });
            
            document.addEventListener('touchstart', function(e) {
                if (!e.target.closest('.shoe-card, .product-card')) {
                    document.querySelectorAll('.shoe-card, .product-card').forEach(c => {
                        c.classList.remove('hover-effect');
                    });
                }
            }, {passive: true});
        });
    }
});














// =============suggest==================
document.addEventListener('DOMContentLoaded', function() {
    const carousel = document.querySelector('.tq12-suggested-carousel');
    const prevBtn = document.querySelector('.tq12-carousel-prev');
    const nextBtn = document.querySelector('.tq12-carousel-next');
    
    if (carousel && prevBtn && nextBtn) {
        const itemWidth = document.querySelector('.tq12-product-card').offsetWidth;
        const scrollAmount = itemWidth * 3; // Scroll 3 items at a time
        
        prevBtn.addEventListener('click', () => {
            carousel.scrollBy({ left: -scrollAmount, behavior: 'smooth' });
        });
        
        nextBtn.addEventListener('click', () => {
            carousel.scrollBy({ left: scrollAmount, behavior: 'smooth' });
        });
        
        // Hide/show buttons based on scroll position
        carousel.addEventListener('scroll', () => {
            const maxScroll = carousel.scrollWidth - carousel.clientWidth;
            prevBtn.style.visibility = carousel.scrollLeft > 0 ? 'visible' : 'hidden';
            nextBtn.style.visibility = carousel.scrollLeft < maxScroll - 5 ? 'visible' : 'hidden';
        });
        
        // Initial state
        prevBtn.style.visibility = 'hidden';
        if (carousel.scrollWidth <= carousel.clientWidth) {
            nextBtn.style.visibility = 'hidden';
        }
    }
});

