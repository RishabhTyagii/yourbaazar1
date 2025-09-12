# from .models import Coupon, CouponUsage
# from datetime import date
# from cart.cart import CartService
# def apply_coupon(request, code):
#     try:
#         coupon = Coupon.objects.get(code=code)
#     except Coupon.DoesNotExist:
#         return {'success': False, 'message': 'Invalid coupon code'}

#     # 🧮 Get total from CartService
#     cart_service = CartService(request)
#     cart_total = cart_service.get_total_price()

#     # 🕒 Expiry check
#     if coupon.expiry_date and coupon.expiry_date < date.today():
#         return {'success': False, 'message': 'Coupon expired'}

#     # 💰 Min cart value check
#     if cart_total < coupon.min_cart_value:
#         return {'success': False, 'message': f'Min cart value ₹{coupon.min_cart_value} required'}

#     # 🔐 First time user only
#     if coupon.first_time_only:
#         if CouponUsage.objects.filter(user=request.user).exists():
#             return {'success': False, 'message': 'Only for first-time users'}

#     # ⛔ One-time use check
#     if coupon.one_time_use:
#         if CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
#             return {'success': False, 'message': 'You already used this coupon'}

#     # 🔢 Max usage check
#     if coupon.max_uses:
#         if CouponUsage.objects.filter(coupon=coupon).count() >= coupon.max_uses:
#             return {'success': False, 'message': 'Coupon usage limit reached'}

#     # ✅ All checks passed
#     discount = coupon.calculate_discount(cart_total)
#     request.session['applied_coupon'] = code

#     return {
#         'success': True,
#         'discount': float(discount),
#         'message': 'Coupon applied successfully'
#     }
#     cart_service = CartService(request)
#     cart_total = cart_service.get_total_price() 
#     try:
#         coupon = Coupon.objects.get(code=code)
#     except Coupon.DoesNotExist:
#         return {'success': False, 'message': 'Invalid coupon code'}

#     if coupon.expiry_date and coupon.expiry_date < date.today():
#         return {'success': False, 'message': 'Coupon expired'}

#      # ✅ FIXED

#     if cart_total < coupon.min_cart_value:
#         return {'success': False, 'message': f'Min cart ₹{coupon.min_cart_value} required'}

#     if coupon.first_time_only and CouponUsage.objects.filter(user=request.user).exists():
#         return {'success': False, 'message': 'First-time users only'}

#     if coupon.one_time_use and CouponUsage.objects.filter(user=request.user, coupon=coupon).exists():
#         return {'success': False, 'message': 'Already used this coupon'}

#     if coupon.max_uses and CouponUsage.objects.filter(coupon=coupon).count() >= coupon.max_uses:
#         return {'success': False, 'message': 'Coupon usage limit reached'}

#     # ✅ Save in session
#     request.session['applied_coupon'] = code
#     return {'success': True, 'message': 'Coupon applied successfully'}