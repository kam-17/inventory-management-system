from functools import wraps
from flask import redirect, url_for, flash, request, abort
from flask_login import current_user

def require_role(allowed_roles):
    """
    Decorator to require specific roles for accessing routes.
    
    Args:
        allowed_roles: String or list of role names that are allowed
    """
    if isinstance(allowed_roles, str):
        allowed_roles = [allowed_roles]
    
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not current_user.is_authenticated:
                flash('Please log in to access this page.', 'warning')
                return redirect(url_for('auth.login', next=request.url))
            
            if not current_user.can_access(allowed_roles):
                flash('You do not have permission to access this page.', 'error')
                abort(403)
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def require_super_admin(f):
    """Decorator to require SUPER_ADMIN role"""
    return require_role('SUPER_ADMIN')(f)

def require_admin(f):
    """Decorator to require ADMIN or SUPER_ADMIN role"""
    return require_role(['ADMIN', 'SUPER_ADMIN'])(f)

def require_office(f):
    """Decorator to require OFFICE, ADMIN, or SUPER_ADMIN role"""
    return require_role(['OFFICE', 'ADMIN', 'SUPER_ADMIN'])(f)

def require_store(f):
    """Decorator to require STORE, ADMIN, or SUPER_ADMIN role"""
    return require_role(['STORE', 'ADMIN', 'SUPER_ADMIN'])(f)

def require_service_entry(f):
    """Decorator to require SERVICE_ENTRY or higher role"""
    return require_role(['SERVICE_ENTRY', 'STORE', 'ADMIN', 'SUPER_ADMIN'])(f)

def log_user_action(action, table_name, record_id=None, old_values=None, new_values=None):
    """
    Log user actions for audit trail
    
    Args:
        action: Action performed (CREATE, UPDATE, DELETE, etc.)
        table_name: Name of the affected table
        record_id: ID of the affected record
        old_values: Previous values (for updates)
        new_values: New values (for updates/creates)
    """
    from models.user import AuditLog
    from app import db
    import json
    
    if current_user.is_authenticated:
        audit_log = AuditLog(
            user_id=current_user.id,
            action=action,
            table_name=table_name,
            record_id=record_id,
            old_values=json.dumps(old_values) if old_values else None,
            new_values=json.dumps(new_values) if new_values else None,
            ip_address=request.remote_addr,
            user_agent=request.user_agent.string[:255] if request.user_agent else None
        )
        
        db.session.add(audit_log)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            # Log to application logs if needed
            pass

def check_otp_required(operation_type):
    """
    Check if OTP is required for the current user and operation
    
    Args:
        operation_type: Type of operation (DELETE, EDIT, etc.)
    
    Returns:
        Boolean indicating if OTP is required
    """
    # SUPER_ADMIN operations always require OTP
    if current_user.has_role('SUPER_ADMIN'):
        return True
    
    # Other sensitive operations that require OTP
    sensitive_operations = ['DELETE', 'APPROVE', 'OVERRIDE']
    
    return operation_type in sensitive_operations

def generate_sequence_number(prefix, model_class, field_name, length=6):
    """
    Generate sequential numbers for documents like DC numbers
    
    Args:
        prefix: Prefix for the number (e.g., 'DC', 'INV')
        model_class: SQLAlchemy model class
        field_name: Field name containing the sequence
        length: Length of the numeric part
    
    Returns:
        Generated sequence number
    """
    from datetime import datetime
    
    # Get current year and month
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # Create prefix with year/month (e.g., DC2024010001)
    date_prefix = f"{prefix}{current_year}{current_month:02d}"
    
    # Find the last number for this prefix
    last_record = model_class.query.filter(
        getattr(model_class, field_name).like(f"{date_prefix}%")
    ).order_by(getattr(model_class, field_name).desc()).first()
    
    if last_record:
        last_number = getattr(last_record, field_name)
        # Extract the numeric part and increment
        numeric_part = int(last_number[-length:])
        new_number = numeric_part + 1
    else:
        new_number = 1
    
    # Format with leading zeros
    return f"{date_prefix}{new_number:0{length}d}"

def format_currency(amount, currency_symbol='₹'):
    """
    Format currency for display
    
    Args:
        amount: Numeric amount
        currency_symbol: Currency symbol to use
    
    Returns:
        Formatted currency string
    """
    if amount is None:
        return f"{currency_symbol}0.00"
    
    return f"{currency_symbol}{amount:,.2f}"

def format_date(date_obj, format_str='%d-%m-%Y'):
    """
    Format date for display
    
    Args:
        date_obj: Date object
        format_str: Format string
    
    Returns:
        Formatted date string
    """
    if date_obj is None:
        return ''
    
    return date_obj.strftime(format_str)

def format_datetime(datetime_obj, format_str='%d-%m-%Y %H:%M'):
    """
    Format datetime for display
    
    Args:
        datetime_obj: Datetime object
        format_str: Format string
    
    Returns:
        Formatted datetime string
    """
    if datetime_obj is None:
        return ''
    
    return datetime_obj.strftime(format_str)

def get_pagination_info(page, per_page, total):
    """
    Get pagination information
    
    Args:
        page: Current page number
        per_page: Items per page
        total: Total number of items
    
    Returns:
        Dictionary with pagination info
    """
    total_pages = (total + per_page - 1) // per_page
    has_prev = page > 1
    has_next = page < total_pages
    
    return {
        'page': page,
        'per_page': per_page,
        'total': total,
        'total_pages': total_pages,
        'has_prev': has_prev,
        'has_next': has_next,
        'prev_num': page - 1 if has_prev else None,
        'next_num': page + 1 if has_next else None
    }