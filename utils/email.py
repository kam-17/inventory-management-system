import random
import string
from datetime import datetime, timedelta
from flask_mail import Message
from flask import current_app
import pyotp
import qrcode
from io import BytesIO
import base64

def generate_otp_code(length=6):
    """Generate a random OTP code"""
    return ''.join(random.choices(string.digits, k=length))

def create_otp_secret():
    """Create a new OTP secret for TOTP"""
    return pyotp.random_base32()

def generate_totp_code(secret):
    """Generate TOTP code using secret"""
    totp = pyotp.TOTP(secret)
    return totp.now()

def verify_totp_code(secret, code, window=1):
    """Verify TOTP code with tolerance window"""
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=window)

def generate_qr_code(secret, user_email, app_name="Inventory System"):
    """Generate QR code for TOTP setup"""
    totp = pyotp.TOTP(secret)
    qr_code_url = totp.provisioning_uri(
        name=user_email,
        issuer_name=app_name
    )
    
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_code_url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for display in HTML
    buffer = BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    qr_code_data = base64.b64encode(buffer.getvalue()).decode()
    
    return f"data:image/png;base64,{qr_code_data}"

def send_otp_email(user, otp_code, purpose="verification"):
    """
    Send OTP via email
    
    Args:
        user: User object
        otp_code: OTP code to send
        purpose: Purpose of the OTP
    """
    from app import mail
    
    subject = f"OTP for {purpose.title()} - Inventory Management System"
    
    body = f"""
    Dear {user.get_full_name()},
    
    Your OTP for {purpose} is: {otp_code}
    
    This OTP is valid for {current_app.config.get('OTP_VALID_DURATION', 300) // 60} minutes.
    Please do not share this code with anyone.
    
    If you did not request this OTP, please contact your system administrator immediately.
    
    Best regards,
    Inventory Management System
    """
    
    html_body = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #333;">OTP Verification</h2>
            <p>Dear <strong>{user.get_full_name()}</strong>,</p>
            
            <p>Your OTP for <strong>{purpose}</strong> is:</p>
            
            <div style="background-color: #f8f9fa; padding: 20px; text-align: center; margin: 20px 0; border-radius: 5px;">
                <h1 style="color: #007bff; font-size: 32px; margin: 0; letter-spacing: 5px;">{otp_code}</h1>
            </div>
            
            <p style="color: #666;">
                This OTP is valid for <strong>{current_app.config.get('OTP_VALID_DURATION', 300) // 60} minutes</strong>.
                Please do not share this code with anyone.
            </p>
            
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <p style="margin: 0; color: #856404;">
                    <strong>Security Notice:</strong> If you did not request this OTP, 
                    please contact your system administrator immediately.
                </p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 12px;">
                Best regards,<br>
                Inventory Management System
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        msg = Message(
            subject=subject,
            recipients=[user.email],
            body=body,
            html=html_body
        )
        mail.send(msg)
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send OTP email to {user.email}: {str(e)}")
        return False

def create_otp_log(user, purpose, otp_code, expires_minutes=5):
    """
    Create OTP log entry in database
    
    Args:
        user: User object
        purpose: Purpose of the OTP
        otp_code: Generated OTP code
        expires_minutes: Expiry time in minutes
    
    Returns:
        OTPLog object
    """
    from models.user import OTPLog
    from app import db
    from flask import request
    
    expires_at = datetime.utcnow() + timedelta(minutes=expires_minutes)
    
    otp_log = OTPLog(
        user_id=user.id,
        otp_code=otp_code,
        purpose=purpose,
        expires_at=expires_at,
        ip_address=request.remote_addr if request else None
    )
    
    db.session.add(otp_log)
    db.session.commit()
    
    return otp_log

def verify_otp(user, otp_code, purpose):
    """
    Verify OTP code for user and purpose
    
    Args:
        user: User object
        otp_code: OTP code to verify
        purpose: Purpose to match
    
    Returns:
        Tuple (success: bool, message: str)
    """
    from models.user import OTPLog
    
    # Find the most recent unused OTP for this user and purpose
    otp_log = OTPLog.query.filter_by(
        user_id=user.id,
        purpose=purpose,
        is_used=False
    ).filter(
        OTPLog.expires_at > datetime.utcnow()
    ).order_by(OTPLog.created_at.desc()).first()
    
    if not otp_log:
        return False, "No valid OTP found or OTP has expired."
    
    if otp_log.otp_code != otp_code:
        return False, "Invalid OTP code."
    
    # Mark OTP as used
    otp_log.mark_used()
    
    from app import db
    db.session.commit()
    
    return True, "OTP verified successfully."

def cleanup_expired_otps():
    """Clean up expired OTP logs"""
    from models.user import OTPLog
    from app import db
    
    expired_otps = OTPLog.query.filter(
        OTPLog.expires_at < datetime.utcnow()
    ).all()
    
    for otp in expired_otps:
        db.session.delete(otp)
    
    db.session.commit()
    return len(expired_otps)

def send_low_stock_alert(materials):
    """
    Send low stock alert email to administrators
    
    Args:
        materials: List of materials with low stock
    """
    from app import mail
    from models.user import User, UserRole
    
    # Get all admin users
    admin_users = User.query.filter(
        User.role.in_([UserRole.ADMIN, UserRole.SUPER_ADMIN]),
        User.is_active == True
    ).all()
    
    if not admin_users or not materials:
        return
    
    subject = "Low Stock Alert - Inventory Management System"
    
    # Prepare material list for email
    material_list = ""
    for material in materials:
        current_stock = material.get_current_stock()
        material_list += f"• {material.material_name} ({material.material_code}): {current_stock} {material.unit_of_measure} (Min: {material.minimum_stock_level})\n"
    
    body = f"""
    Low Stock Alert
    
    The following materials are running low in stock:
    
    {material_list}
    
    Please take necessary action to replenish the stock.
    
    Inventory Management System
    """
    
    html_body = f"""
    <html>
    <body>
        <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
            <h2 style="color: #dc3545;">⚠️ Low Stock Alert</h2>
            
            <p>The following materials are running low in stock:</p>
            
            <div style="background-color: #f8f9fa; padding: 15px; border-radius: 5px; margin: 20px 0;">
                <ul style="margin: 0; padding-left: 20px;">
    """
    
    for material in materials:
        current_stock = material.get_current_stock()
        html_body += f"""
                    <li style="margin: 10px 0;">
                        <strong>{material.material_name}</strong> ({material.material_code})<br>
                        <span style="color: #dc3545;">Current: {current_stock} {material.unit_of_measure}</span> | 
                        <span style="color: #6c757d;">Minimum: {material.minimum_stock_level} {material.unit_of_measure}</span>
                    </li>
        """
    
    html_body += """
                </ul>
            </div>
            
            <div style="background-color: #fff3cd; border: 1px solid #ffeaa7; padding: 15px; margin: 20px 0; border-radius: 5px;">
                <p style="margin: 0; color: #856404;">
                    <strong>Action Required:</strong> Please take necessary action to replenish the stock.
                </p>
            </div>
            
            <hr style="border: none; border-top: 1px solid #eee; margin: 30px 0;">
            <p style="color: #999; font-size: 12px;">
                Inventory Management System<br>
                Automated Alert
            </p>
        </div>
    </body>
    </html>
    """
    
    try:
        for admin in admin_users:
            msg = Message(
                subject=subject,
                recipients=[admin.email],
                body=body,
                html=html_body
            )
            mail.send(msg)
        
        return True
    except Exception as e:
        current_app.logger.error(f"Failed to send low stock alert: {str(e)}")
        return False