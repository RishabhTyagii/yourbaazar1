  // Toggle password visibility
  document.querySelector('.toggle-password').addEventListener('click', function(e) {
    const passwordInput = document.querySelector('#new_password');
    const icon = this.querySelector('i');
    
    if (passwordInput.type === 'password') {
      passwordInput.type = 'text';
      icon.classList.replace('fa-eye', 'fa-eye-slash');
    } else {
      passwordInput.type = 'password';
      icon.classList.replace('fa-eye-slash', 'fa-eye');
    }
  });

  // Password strength indicator (basic example)
  document.querySelector('#new_password').addEventListener('input', function() {
    const strengthMeter = document.querySelector('.strength-meter');
    const segments = strengthMeter.querySelectorAll('.strength-segment');
    const strengthText = document.querySelector('.strength-text');
    const password = this.value;
    
    // Reset
    segments.forEach(seg => seg.style.background = 'var(--gray)');
    strengthText.textContent = 'Password strength';
    
    if (password.length > 0) {
      // Very basic strength calculation
      let strength = 0;
      if (password.length >= 8) strength++;
      if (password.match(/[A-Z]/)) strength++;
      if (password.match(/[0-9]/)) strength++;
      if (password.match(/[^A-Za-z0-9]/)) strength++;
      
      // Update UI
      if (strength > 0) {
        segments[0].style.background = 'var(--danger)';
        strengthText.textContent = 'Weak';
      }
      if (strength > 2) {
        segments[1].style.background = 'var(--warning)';
        strengthText.textContent = 'Medium';
      }
      if (strength > 3) {
        segments[2].style.background = 'var(--success)';
        strengthText.textContent = 'Strong';
      }
    }
  });

  // Countdown timer for OTP resend (example)
  let timeLeft = 119; // 1 minute 59 seconds
  const countdownElement = document.getElementById('countdown');
  const resendLink = document.getElementById('resend-link');
  
  resendLink.style.display = 'none';
  
  const timer = setInterval(() => {
    const minutes = Math.floor(timeLeft / 60);
    const seconds = timeLeft % 60;
    
    countdownElement.textContent = `You can request a new code in ${minutes}:${seconds < 10 ? '0' + seconds : seconds}`;
    
    if (timeLeft <= 0) {
      clearInterval(timer);
      countdownElement.style.display = 'none';
      resendLink.style.display = 'inline';
    }
    
    timeLeft--;
  }, 1000);