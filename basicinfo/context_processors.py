from .models import NavImage

def basicinfo_context(request):
    basicinfo = NavImage.objects.first()
    
    nav_image_url = basicinfo.logo_image.url if basicinfo and basicinfo.logo_image else ''

    return {
        'nav_image': nav_image_url,
        'basicinfo': basicinfo,  # optional full object for other fields
    }