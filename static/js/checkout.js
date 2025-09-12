document.addEventListener('DOMContentLoaded', function() {
  var payBtn = document.getElementById('rzp-pay-btn');
  if (payBtn) {
    payBtn.onclick = function(e) {
      e.preventDefault();
      var rzp = new Razorpay({
        "key": "{{ razorpay_key_id|default:'' }}",
        "amount": Math.round(Number("{{ summary.total|default:0 }}") * 100),
        "currency": "INR",
        "name": "Your Bazaar",
        "description": "Order Payment",
        "order_id": "{{ razorpay_order_id|default:'' }}",
        "handler": function(response) {
          document.getElementById('razorpay_payment_id').value = response.razorpay_payment_id;
          document.getElementById('payment_method').value = "online";
          document.getElementById('checkout-form').submit();
        },
        "prefill": {
          "name": "{{ request.user.get_full_name|default:'Guest User' }}",
          "email": "{{ request.user.email|default:'test@example.com' }}",
          "contact": "{{ request.user.phone|default:'9999999999' }}"
        },
        "theme": { "color": "#6c5ce7" },
        "modal": {
          "ondismiss": function() { }
        }
      });
      rzp.open();
    };
  }
});