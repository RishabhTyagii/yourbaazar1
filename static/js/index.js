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









document.addEventListener('DOMContentLoaded', function() {
      const carousel = document.querySelector('.xxx-course-carousel');
      const track = document.querySelector('.xxx-carousel-track');
      const items = document.querySelectorAll('.xxx-carousel-item');
      const prevBtn = document.querySelector('.xxx-carousel-prev');
      const nextBtn = document.querySelector('.xxx-carousel-next');
      
      let currentIndex = 2; // Center item is active by default
      let autoPlayInterval;
      
      // Initialize carousel
      function initCarousel() {
        updateCarousel();
        startAutoPlay();
        
        // Handle navigation
        prevBtn.addEventListener('click', () => {
          rotateCarousel(-1);
          resetAutoPlay();
        });
        
        nextBtn.addEventListener('click', () => {
          rotateCarousel(1);
          resetAutoPlay();
        });
        
        // Pause autoplay on hover
        carousel.addEventListener('mouseenter', pauseAutoPlay);
        carousel.addEventListener('mouseleave', startAutoPlay);
      }
      
      // Rotate carousel items
      function rotateCarousel(direction) {
        currentIndex += direction;
        
        if (currentIndex < 0) {
          currentIndex = items.length - 1;
        } else if (currentIndex >= items.length) {
          currentIndex = 0;
        }
        
        updateCarousel();
      }
      
      // Update carousel positions
      function updateCarousel() {
        items.forEach((item, index) => {
          item.classList.remove('xxx-active');
          
          // Calculate position based on currentIndex
          let position = (index - currentIndex + items.length) % items.length;
          
          if (position === 0) {
            item.style.left = '5%';
            item.style.width = '15%';
            item.style.height = '180px';
            item.style.top = '60px';
            item.style.zIndex = '1';
          } else if (position === 1 || position === items.length - 1) {
            item.style.left = position === 1 ? '20%' : '65%';
            item.style.width = '20%';
            item.style.height = '220px';
            item.style.top = '40px';
            item.style.zIndex = '2';
          } else if (position === 2 || position === items.length - 2) {
            item.style.left = position === 2 ? '40%' : '80%';
            item.style.width = position === 2 ? '25%' : '15%';
            item.style.height = position === 2 ? '260px' : '180px';
            item.style.top = position === 2 ? '20px' : '60px';
            item.style.zIndex = position === 2 ? '3' : '1';
          }
          
          // Mobile adjustments
          if (window.innerWidth <= 768) {
            if (position === 0) {
              item.style.left = '2%';
              item.style.width = '18%';
              item.style.height = '140px';
              item.style.top = '40px';
            } else if (position === 1 || position === items.length - 1) {
              item.style.left = position === 1 ? '20%' : '74%';
              item.style.width = '24%';
              item.style.height = '170px';
              item.style.top = '25px';
            } else if (position === 2 || position === items.length - 2) {
              item.style.left = position === 2 ? '44%' : '80%';
              item.style.width = position === 2 ? '30%' : '18%';
              item.style.height = position === 2 ? '200px' : '140px';
              item.style.top = position === 2 ? '10px' : '40px';
            }
          }
          
          // Small mobile adjustments
          if (window.innerWidth <= 480) {
            if (position === 0) {
              item.style.left = '0%';
              item.style.width = '20%';
              item.style.height = '110px';
              item.style.top = '35px';
            } else if (position === 1 || position === items.length - 1) {
              item.style.left = position === 1 ? '20%' : '70%';
              item.style.width = '26%';
              item.style.height = '140px';
              item.style.top = '20px';
            } else if (position === 2 || position === items.length - 2) {
              item.style.left = position === 2 ? '46%' : '80%';
              item.style.width = position === 2 ? '34%' : '20%';
              item.style.height = position === 2 ? '160px' : '110px';
              item.style.top = position === 2 ? '10px' : '35px';
            }
          }
        });
        
        // Set active item
        items[currentIndex].classList.add('xxx-active');
      }
      
      // Autoplay functions
      function startAutoPlay() {
        autoPlayInterval = setInterval(() => {
          rotateCarousel(1);
        }, 3000);
      }
      
      function pauseAutoPlay() {
        clearInterval(autoPlayInterval);
      }
      
      function resetAutoPlay() {
        pauseAutoPlay();
        startAutoPlay();
      }
      
      // Handle window resize
      window.addEventListener('resize', updateCarousel);
      
      // Initialize
      initCarousel();
    });




 document.addEventListener('DOMContentLoaded', function() {
      const carousel = document.querySelector('.fpsc1-product-carousel');
      const track = document.querySelector('.fpsc1-carousel-track');
      const cards = document.querySelectorAll('.fpsc1-product-card');
      const prevBtn = document.querySelector('.fpsc1-carousel-prev');
      const nextBtn = document.querySelector('.fpsc1-carousel-next');
      
      let currentIndex = 0;
      let autoPlayInterval;
      const cardWidth = cards[0].offsetWidth;
      const gap = 5;
      
      // Initialize carousel
      function initCarousel() {
        updateActiveCard();
        startAutoPlay();
        
        // Handle navigation
        prevBtn.addEventListener('click', () => {
          moveCarousel(-1);
          resetAutoPlay();
        });
        
        nextBtn.addEventListener('click', () => {
          moveCarousel(1);
          resetAutoPlay();
        });
        
        // Pause autoplay on hover
        carousel.addEventListener('mouseenter', pauseAutoPlay);
        carousel.addEventListener('mouseleave', startAutoPlay);
      }
      
      // Move carousel
      function moveCarousel(direction) {
        currentIndex += direction;
        
        if (currentIndex < 0) {
          currentIndex = cards.length - 1;
        } else if (currentIndex >= cards.length) {
          currentIndex = 0;
        }
        
        const scrollPosition = currentIndex * (cardWidth + gap);
        track.scrollTo({
          left: scrollPosition,
          behavior: 'smooth'
        });
        
        updateActiveCard();
      }
      
      // Update active card
      function updateActiveCard() {
        cards.forEach((card, index) => {
          card.classList.remove('fpsc1-active');
          if (index === currentIndex) {
            card.classList.add('fpsc1-active');
          }
        });
      }
      
      // Handle scroll events
      track.addEventListener('scroll', () => {
        const scrollPosition = track.scrollLeft;
        currentIndex = Math.round(scrollPosition / (cardWidth + gap));
        updateActiveCard();
      });
      
      // Autoplay functions
      function startAutoPlay() {
        autoPlayInterval = setInterval(() => {
          moveCarousel(1);
        }, 3000);
      }
      
      function pauseAutoPlay() {
        clearInterval(autoPlayInterval);
      }
      
      function resetAutoPlay() {
        pauseAutoPlay();
        startAutoPlay();
      }
      
      // Handle window resize
      window.addEventListener('resize', () => {
        const newCardWidth = cards[0].offsetWidth;
        if (newCardWidth !== cardWidth) {
          const scrollPosition = currentIndex * (newCardWidth + gap);
          track.scrollTo({
            left: scrollPosition,
            behavior: 'auto'
          });
        }
      });
      
      // Initialize
      initCarousel();
    });


 document.addEventListener('DOMContentLoaded', function() {
      const carousel = document.querySelector('.fpsc-product-carousel');
      const track = document.querySelector('.fpsc-carousel-track');
      const cards = document.querySelectorAll('.fpsc-product-card');
      const prevBtn = document.querySelector('.fpsc-carousel-prev');
      const nextBtn = document.querySelector('.fpsc-carousel-next');
      
      let currentIndex = 0;
      let autoPlayInterval;
      const cardWidth = cards[0].offsetWidth;
      const gap = 5;
      
      // Initialize carousel
      function initCarousel() {
        updateActiveCard();
        startAutoPlay();
        
        // Handle navigation
        prevBtn.addEventListener('click', () => {
          moveCarousel(-1);
          resetAutoPlay();
        });
        
        nextBtn.addEventListener('click', () => {
          moveCarousel(1);
          resetAutoPlay();
        });
        
        // Pause autoplay on hover
        carousel.addEventListener('mouseenter', pauseAutoPlay);
        carousel.addEventListener('mouseleave', startAutoPlay);
      }
      
      // Move carousel
      function moveCarousel(direction) {
        currentIndex += direction;
        
        if (currentIndex < 0) {
          currentIndex = cards.length - 1;
        } else if (currentIndex >= cards.length) {
          currentIndex = 0;
        }
        
        const scrollPosition = currentIndex * (cardWidth + gap);
        track.scrollTo({
          left: scrollPosition,
          behavior: 'smooth'
        });
        
        updateActiveCard();
      }
      
      // Update active card
      function updateActiveCard() {
        cards.forEach((card, index) => {
          card.classList.remove('fpsc-active');
          if (index === currentIndex) {
            card.classList.add('fpsc-active');
          }
        });
      }
      
      // Handle scroll events
      track.addEventListener('scroll', () => {
        const scrollPosition = track.scrollLeft;
        currentIndex = Math.round(scrollPosition / (cardWidth + gap));
        updateActiveCard();
      });
      
      // Autoplay functions
      function startAutoPlay() {
        autoPlayInterval = setInterval(() => {
          moveCarousel(1);
        }, 1500);
      }
      
      function pauseAutoPlay() {
        clearInterval(autoPlayInterval);
      }
      
      function resetAutoPlay() {
        pauseAutoPlay();
        startAutoPlay();
      }
      
      // Handle window resize
      window.addEventListener('resize', () => {
        const newCardWidth = cards[0].offsetWidth;
        if (newCardWidth !== cardWidth) {
          const scrollPosition = currentIndex * (newCardWidth + gap);
          track.scrollTo({
            left: scrollPosition,
            behavior: 'auto'
          });
        }
      });
      
      // Initialize
      initCarousel();
    });




 document.addEventListener('DOMContentLoaded', function() {
      const carousel = document.querySelector('.fpsc2-product-carousel');
      const track = document.querySelector('.fpsc2-carousel-track');
      const cards = document.querySelectorAll('.fpsc2-product-card');
      const prevBtn = document.querySelector('.fpsc2-carousel-prev');
      const nextBtn = document.querySelector('.fpsc2-carousel-next');
      
      let currentIndex = 0;
      let autoPlayInterval;
      const cardWidth = cards[0].offsetWidth;
      const gap = 5;
      
      // Initialize carousel
      function initCarousel() {
        updateActiveCard();
        startAutoPlay();
        
        // Handle navigation
        prevBtn.addEventListener('click', () => {
          moveCarousel(-1);
          resetAutoPlay();
        });
        
        nextBtn.addEventListener('click', () => {
          moveCarousel(1);
          resetAutoPlay();
        });
        
        // Pause autoplay on hover
        carousel.addEventListener('mouseenter', pauseAutoPlay);
        carousel.addEventListener('mouseleave', startAutoPlay);
      }
      
      // Move carousel
      function moveCarousel(direction) {
        currentIndex += direction;
        
        if (currentIndex < 0) {
          currentIndex = cards.length - 1;
        } else if (currentIndex >= cards.length) {
          currentIndex = 0;
        }
        
        const scrollPosition = currentIndex * (cardWidth + gap);
        track.scrollTo({
          left: scrollPosition,
          behavior: 'smooth'
        });
        
        updateActiveCard();
      }
      
      // Update active card
      function updateActiveCard() {
        cards.forEach((card, index) => {
          card.classList.remove('fpsc2-active');
          if (index === currentIndex) {
            card.classList.add('fpsc2-active');
          }
        });
      }
      
      // Handle scroll events
      track.addEventListener('scroll', () => {
        const scrollPosition = track.scrollLeft;
        currentIndex = Math.round(scrollPosition / (cardWidth + gap));
        updateActiveCard();
      });
      
      // Autoplay functions
      function startAutoPlay() {
        autoPlayInterval = setInterval(() => {
          moveCarousel(1);
        }, 1000);
      }
      
      function pauseAutoPlay() {
        clearInterval(autoPlayInterval);
      }
      
      function resetAutoPlay() {
        pauseAutoPlay();
        startAutoPlay();
      }
      
      // Handle window resize
      window.addEventListener('resize', () => {
        const newCardWidth = cards[0].offsetWidth;
        if (newCardWidth !== cardWidth) {
          const scrollPosition = currentIndex * (newCardWidth + gap);
          track.scrollTo({
            left: scrollPosition,
            behavior: 'auto'
          });
        }
      });
      
      // Initialize
      initCarousel();
    });

