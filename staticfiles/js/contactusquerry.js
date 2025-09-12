  $(document).ready(function(){
    $(".toggle-status").click(function(){
      const button = $(this);
      const queryId = button.data("id");

      $.ajax({
        url: "{% url 'basicinfo:toggle_query_status' %}",
        type: "POST",
        data: {
          id: queryId,
          csrfmiddlewaretoken: "{{ csrf_token }}"
        },
        success: function(response){
          if(response.success){
            if(response.new_status) {
              button.html('<span class="status-icon">✓</span> Resolved');
              button.removeClass('unresolved').addClass('resolved');
            } else {
              button.html('<span class="status-icon">✗</span> Unresolved');
              button.removeClass('resolved').addClass('unresolved');
            }
          }
        }
      });
    });
  });