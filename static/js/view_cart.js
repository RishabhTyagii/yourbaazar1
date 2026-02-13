$(function() {
  function getCookie(name) {
      let cookieValue = null;
      if (document.cookie && document.cookie !== '') {
          const cookies = document.cookie.split(';');
          for (let i = 0; i < cookies.length; i++) {
              const cookie = $.trim(cookies[i]);
              if (cookie.substring(0, name.length + 1) === (name + '=')) {
                  cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                  break;
              }
          }
      }
      return cookieValue;
  }
  const csrftoken = getCookie('csrftoken');

  function showMessage(message, isError = false) {
    $('#message').text(message).css('color', isError ? '#e22c2c' : '#1fa863').stop(true).fadeIn(80).delay(3000).fadeOut(120);
  }

  // Quantity update using +/− buttons
  $('.qty-plus').click(function() {
    const itemId = $(this).data('item-id');
    let qtyInput = $('#qty-input-' + itemId);
    let newQty = parseInt(qtyInput.val()) + 1;
    updateQuantity(itemId, newQty, qtyInput);
  });

  $('.qty-minus').click(function() {
    const itemId = $(this).data('item-id');
    let qtyInput = $('#qty-input-' + itemId);
    let newQty = Math.max(1, parseInt(qtyInput.val()) - 1);
    updateQuantity(itemId, newQty, qtyInput);
  });

  function updateQuantity(itemId, quantity, qtyInput) {
    $.ajax({
      url: "{% url 'update_cart_item' 0 %}".replace(/0/, itemId),
      type: 'POST',
      data: { 'quantity': quantity },
      headers: { 'X-CSRFToken': csrftoken },
      success: function(response) {
        if (response.success) {
          qtyInput.val(quantity);
          $('#cart-subtotal').text(response.cart_summary.subtotal);
          $('#cart-shipping').text(response.cart_summary.shipping);
          $('#cart-discount').text(response.cart_summary.discount);
          $('#cart-total').text(response.cart_summary.total);
          $(`tr[data-item-id="${itemId}"] td.col-subtotal`).text('₹' + (parseFloat(response.cart_summary.subtotal)).toFixed(2));
          // Disable minus button if qty==1
          qtyInput.closest('.qty-selector').find('.qty-minus').prop('disabled', quantity <= 1);
          showMessage(response.message);
        } else {
          showMessage(response.message, true);
        }
      },
      error: function() { showMessage('Error updating cart. Please try again.', true); }
    });
  }

  // Remove cart item
  $('.remove-cart-item').on('click', function() {
    const itemId = $(this).data('item-id');
    $.ajax({
      url: "{% url 'remove_cart_item' 0 %}".replace(/0/, itemId),
      type: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      success: function(response) {
        if (response.success) {
          $(`tr[data-item-id="${itemId}"]`).remove();
          $('#cart-subtotal').text(response.cart_summary.subtotal);
          $('#cart-shipping').text(response.cart_summary.shipping);
          $('#cart-discount').text(response.cart_summary.discount);
          $('#cart-total').text(response.cart_summary.total);
          showMessage(response.message);
          if ($('tbody tr').length === 0) location.reload();
        } else {
          showMessage(response.message, true);
        }
      },
      error: function() {
        showMessage('Error removing item. Please try again.', true);
      }
    });
  });

  // Apply coupon
  $('#apply-coupon-btn').click(function() {
    const code = $('#coupon-code-input').val().trim();
    if (!code) { showMessage('Please enter a coupon code.', true); return; }
    $.ajax({
      url: "{% url 'apply_coupon' %}",
      type: 'POST',
      contentType: 'application/json',
      data: JSON.stringify({ code: code }),
      headers: { 'X-CSRFToken': csrftoken },
      success: function(response) {
        if (response.success) { showMessage(response.message); location.reload(); }
        else { showMessage(response.message, true); }
      },
      error: function() { showMessage('Error applying coupon. Please try again.', true); }
    });
  });

  // Remove coupon
  $('#remove-coupon-btn').click(function() {
    $.ajax({
      url: "{% url 'remove_coupon' %}",
      type: 'POST',
      headers: { 'X-CSRFToken': csrftoken },
      success: function(response) {
        if (response.success) { showMessage(response.message); location.reload(); }
        else { showMessage(response.message, true); }
      },
      error: function() { showMessage('Error removing coupon. Please try again.', true); }
    });
  });
});