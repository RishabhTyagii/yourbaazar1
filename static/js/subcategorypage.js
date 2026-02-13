    // Particles.js configuration
    document.addEventListener('DOMContentLoaded', function() {
        // Create particles
        const particlesEl = document.getElementById('particles-js');
        for (let i = 0; i < 30; i++) {
            const particle = document.createElement('div');
            particle.classList.add('particle');
            
            // Random size between 5px and 15px
            const size = Math.random() * 10 + 5;
            particle.style.width = `${size}px`;
            particle.style.height = `${size}px`;
            
            // Random position
            particle.style.left = `${Math.random() * 100}%`;
            particle.style.top = `${Math.random() * 100}%`;
            
            // Random animation duration
            particle.style.animationDuration = `${Math.random() * 10 + 10}s`;
            particle.style.animationDelay = `${Math.random() * 5}s`;
            
            particlesEl.appendChild(particle);
        }
        
        // Add hover tilt effect to cards
        const cards = document.querySelectorAll('.product-card');
        cards.forEach(card => {
            card.addEventListener('mousemove', (e) => {
                const x = e.clientX - card.getBoundingClientRect().left;
                const y = e.clientY - card.getBoundingClientRect().top;
                
                const centerX = card.offsetWidth / 2;
                const centerY = card.offsetHeight / 2;
                
                const angleX = (y - centerY) / 20;
                const angleY = (centerX - x) / 20;
                
                card.style.transform = `perspective(1000px) rotateX(${angleX}deg) rotateY(${angleY}deg) translateY(-10px)`;
            });
            
            card.addEventListener('mouseleave', () => {
                card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(-10px)';
            });
        });
    });