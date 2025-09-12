


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

