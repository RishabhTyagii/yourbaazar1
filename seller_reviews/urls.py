from django.urls import path
from . import views

app_name = "seller_reviews"

urlpatterns = [
    path("testomonial/", views.testimonial_list, name="testimonial_list"),         # View all + pagination
    path("create/", views.testimonial_create, name="testimonial_create"),  # Create/Update (single per seller)
]
