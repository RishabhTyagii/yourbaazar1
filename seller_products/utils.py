from django.core.mail import send_mail
from django.conf import settings

def notify_admin_new_draft(seller_email, seller_username, draft_id, product_name, sku):
    subject = "New Product Draft Submitted"
    message = f"Seller {seller_username} ({seller_email}) submitted a product draft.\nDraft ID: {draft_id}\nProduct: {product_name}\nSKU: {sku}\nPlease review and approve/reject in admin."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_NOTIFY_EMAIL], fail_silently=False)

def notify_seller_approved(to_email, product_name, product_id):
    subject = "Your Product is Approved"
    message = f"Congratulations! Your product '{product_name}' has been approved.\nProduct ID: {product_id}."
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)

def notify_seller_rejected(to_email, product_name, draft_id, reason):
    subject = "Your Product was Rejected"
    message = f"Your product draft '{product_name}' (Draft ID: {draft_id}) was rejected.\nReason: {reason}"
    send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [to_email], fail_silently=False)


