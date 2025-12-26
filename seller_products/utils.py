from django.core.mail import send_mail
from django.conf import settings
from django.core.mail import EmailMultiAlternatives

def notify_admin_new_draft(seller_email, seller_username, draft_id, product_name, sku):
    subject = "📦 New Product Draft Submitted - YourBaazar"

    html_content = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; padding:30px; background-color:#f4f6f9;">
      <div style="max-width:600px; margin:auto; background:#ffffff; border-radius:12px; padding:25px; border:1px solid #e5e7eb; box-shadow:0 4px 12px rgba(0,0,0,0.05);">
        
        <!-- Logo -->
        <div style="text-align:center; margin-bottom:25px;">
          <img src="https://yourbaazar.com/static/icon/logo.png" alt="YourBaazar Logo" style="height:55px;">
        </div>

        <!-- Title -->
        <h2 style="color:#1e3a8a; text-align:center; margin-bottom:20px; font-weight:600;">
          New Product Draft Submitted
        </h2>

        <!-- Seller Info -->
        <p style="font-size:15px; color:#333; margin:0 0 12px 0;">
          A seller has submitted a new product draft for review.
        </p>
        <div style="background:#f1f5f9; padding:14px; border-left:5px solid #1e3a8a; margin:20px 0; font-size:14px; color:#111827; border-radius:6px;">
          <strong>Seller:</strong> {seller_username} ({seller_email})<br>
          <strong>Draft ID:</strong> {draft_id}<br>
          <strong>Product:</strong> {product_name}<br>
          <strong>SKU:</strong> {sku}
        </div>

        <!-- Call to Action -->
        <p style="font-size:14px; color:#444; margin:0 0 15px 0;">
          Please review and <strong>approve or reject</strong> this draft in the admin dashboard.
        </p>

        <!-- Footer -->
        <p style="margin-top:25px; font-size:13px; color:#555; text-align:center;">
          Regards,<br>
          <strong>YourBaazar System</strong>
        </p>
      </div>

      <!-- Bottom Note -->
      <p style="text-align:center; font-size:12px; color:#888; margin-top:20px;">
        © {2025} YourBaazar. All rights reserved.
      </p>
    </div>
    """

    email = EmailMultiAlternatives(subject, "", settings.DEFAULT_FROM_EMAIL, [settings.ADMIN_NOTIFY_EMAIL])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)

def notify_seller_approved(to_email, product_name, product_id):
    subject = "✅ Product Approved - YourBaazar"

    html_content = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; padding:30px; background-color:#f4f6f9;">
      <div style="max-width:600px; margin:auto; background:#ffffff; border-radius:12px; padding:25px; border:1px solid #e5e7eb; box-shadow:0 4px 12px rgba(0,0,0,0.05);">
        
        <!-- Logo -->
        <div style="text-align:center; margin-bottom:25px;">
          <img src="https://yourbaazar.com/static/icon/logo.png" alt="YourBaazar Logo" style="height:55px;">
        </div>

        <!-- Title -->
        <h2 style="color:#2e7d32; text-align:center; margin-bottom:20px; font-weight:600;">
          🎉 Product Approved!
        </h2>

        <!-- Message -->
        <p style="font-size:15px; color:#333; line-height:1.6; margin:0 0 15px 0;">
          Congratulations! Your product 
          <strong>{product_name}</strong> 
          has been successfully approved and is now live on YourBaazar.
        </p>

        <!-- Product Info -->
        <div style="background:#e8f5e9; padding:14px; border-left:5px solid #2e7d32; margin:20px 0; color:#1b5e20; font-size:14px; border-radius:6px;">
          <strong>Product ID:</strong> {product_id}
        </div>

        <!-- Next Steps -->
        <p style="font-size:14px; color:#444; line-height:1.6; margin:0 0 15px 0;">
          You can now manage your product, update stock, and track performance from your seller dashboard.
        </p>

        <!-- Footer -->
        <p style="margin-top:25px; font-size:14px; color:#555; text-align:center;">
          Regards,<br>
          <strong>YourBaazar Team</strong>
        </p>

      </div>

      <!-- Bottom Note -->
      <p style="text-align:center; font-size:12px; color:#888; margin-top:20px;">
        © {2025} YourBaazar. All rights reserved.
      </p>
    </div>
    """

    email = EmailMultiAlternatives(subject, "", settings.DEFAULT_FROM_EMAIL, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)



def notify_seller_rejected(to_email, product_name, draft_id, reason):
    subject = "🚫 Product Draft Rejected - YourBaazar"

    html_content = f"""
    <div style="font-family: 'Segoe UI', Arial, sans-serif; padding:30px; background-color:#f4f6f9;">
      <div style="max-width:600px; margin:auto; background:#ffffff; border-radius:12px; padding:25px; border:1px solid #e5e7eb; box-shadow:0 4px 12px rgba(0,0,0,0.05);">
        
        <!-- Logo -->
        <div style="text-align:center; margin-bottom:25px;">
          <img src="https://yourbaazar.com/static/icon/logo.png" alt="YourBaazar Logo" style="height:55px;">
        </div>

        <!-- Title -->
        <h2 style="color:#e63946; text-align:center; margin-bottom:20px; font-weight:600;">
          Product Draft Rejected
        </h2>

        <!-- Message -->
        <p style="font-size:15px; color:#333; line-height:1.6; margin:0 0 15px 0;">
          Dear Seller,
        </p>
        <p style="font-size:15px; color:#333; line-height:1.6; margin:0 0 15px 0;">
          Unfortunately, your product draft 
          <strong>{product_name}</strong> 
          (Draft ID: <strong>{draft_id}</strong>) has been rejected.
        </p>

        <!-- Reason -->
        <div style="background:#ffecec; padding:14px; border-left:5px solid #e63946; margin:20px 0; color:#b71c1c; font-size:14px; border-radius:6px;">
          <strong>Reason:</strong> {reason}
        </div>

        <!-- Next Steps -->
        <p style="font-size:14px; color:#444; line-height:1.6; margin:0 0 15px 0;">
          You may edit the draft and resubmit it for approval.  
          Please ensure your product details meet our listing guidelines.
        </p>

        <!-- Footer -->
        <p style="margin-top:25px; font-size:14px; color:#555; text-align:center;">
          Regards,<br>
          <strong>YourBaazar Team</strong>
        </p>

      </div>

      <!-- Bottom Note -->
      <p style="text-align:center; font-size:12px; color:#888; margin-top:20px;">
        © {2025} YourBaazar. All rights reserved.
      </p>
    </div>
    """

    email = EmailMultiAlternatives(subject, "", settings.DEFAULT_FROM_EMAIL, [to_email])
    email.attach_alternative(html_content, "text/html")
    email.send(fail_silently=False)


