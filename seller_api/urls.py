# seller_api/urls.py
from django.urls import path
from .views import seller_token_view, create_full_draft, upload_color_images , category_list, subcategory_list, product_type_list, sku_list_view
urlpatterns = [
    path("seller/auth/token/", seller_token_view),
    path("seller/drafts/full-create/", create_full_draft),
    path("seller/drafts/colors/<int:color_id>/images/", upload_color_images),

    # META APIs
path("meta/categories/", category_list),
path("meta/subcategories/", subcategory_list),
path("meta/product-types/", product_type_list),
path("meta/skus/", sku_list_view),


]
# yb_fcd26a8fecc4d0d892fecba19453b6ad       111d96df1fa90a6741bb825f4f659f2e29514a0c8783ea326da97691af9b7da8  
# 
# 
# 