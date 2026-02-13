        document.addEventListener('DOMContentLoaded', function() {
            const resendBtn = document.getElementById('resendBtn');
            const countdownElement = document.getElementById('countdown');
            let cooldownTime = 60; // 1 minute in seconds
            
            // Check if cooldown is active from previous session
            const lastResendTime = localStorage.getItem('lastResendTime');
            if (lastResendTime) {
                const currentTime = Math.floor(Date.now() / 1000);
                const elapsedTime = currentTime - parseInt(lastResendTime);
                
                if (elapsedTime < cooldownTime) {
                    cooldownTime = cooldownTime - elapsedTime;
                    startCountdown();
                }
            }
            
            resendBtn.addEventListener('click', function(e) {
                e.preventDefault();
                
                // Set the current timestamp in localStorage
                localStorage.setItem('lastResendTime', Math.floor(Date.now() / 1000));
                
                // Start countdown
                cooldownTime = 60;
                startCountdown();
                
                // Make AJAX request to resend OTP
                fetch("{% url 'resend_otp' %}", {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': '{{ csrf_token }}',
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('New OTP has been sent to your email!');
                    } else {
                        alert('Failed to resend OTP. Please try again later.');
                    }
                });
            });
            
            function startCountdown() {
                resendBtn.classList.add('disabled');
                countdownElement.textContent = `(0:${cooldownTime < 10 ? '0' : ''}${cooldownTime})`;
                
                const countdownInterval = setInterval(function() {
                    cooldownTime--;
                    
                    if (cooldownTime <= 0) {
                        clearInterval(countdownInterval);
                        resendBtn.classList.remove('disabled');
                        countdownElement.textContent = '';
                        localStorage.removeItem('lastResendTime');
                    } else {
                        countdownElement.textContent = `(0:${cooldownTime < 10 ? '0' : ''}${cooldownTime})`;
                    }
                }, 1000);
            }
        }); 