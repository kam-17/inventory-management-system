from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from utils.auth import require_service_entry
from models.dgset import DGSetDetail, ServiceLog
from models.user import User
from extensions import db
from sqlalchemy import desc, func
from datetime import datetime, timedelta

service_bp = Blueprint('service', __name__)

@service_bp.route('/dashboard')
@login_required
@require_service_entry
def dashboard():
    """Service dashboard for DG set maintenance"""
    
    # Get service statistics
    stats = {
        'total_dg_sets': DGSetDetail.query.filter_by(is_active=True).count(),
        'services_today': ServiceLog.query.filter(
            func.date(ServiceLog.service_date) == datetime.utcnow().date()
        ).count(),
        'services_this_month': ServiceLog.query.filter(
            func.year(ServiceLog.service_date) == datetime.utcnow().year,
            func.month(ServiceLog.service_date) == datetime.utcnow().month
        ).count(),
        'overdue_services': 0,  # Will calculate below
        'my_service_logs': ServiceLog.query.filter_by(created_by=current_user.id).count()
    }
    
    # Calculate overdue services
    overdue_count = 0
    dg_sets = DGSetDetail.query.filter_by(is_active=True).all()
    for dg_set in dg_sets:
        if dg_set.next_service_due and dg_set.next_service_due < datetime.utcnow().date():
            overdue_count += 1
    
    stats['overdue_services'] = overdue_count
    
    # Get recent service logs
    recent_services = ServiceLog.query.order_by(
        desc(ServiceLog.created_at)
    ).limit(10).all()
    
    # Get my recent service logs
    my_recent_services = ServiceLog.query.filter_by(
        created_by=current_user.id
    ).order_by(desc(ServiceLog.created_at)).limit(5).all()
    
    # Get DG sets needing service (next 30 days)
    upcoming_services = []
    future_date = datetime.utcnow().date() + timedelta(days=30)
    
    for dg_set in dg_sets:
        if (dg_set.next_service_due and 
            dg_set.next_service_due <= future_date):
            
            days_until_service = (dg_set.next_service_due - datetime.utcnow().date()).days
            upcoming_services.append({
                'dg_set': dg_set,
                'days_until_service': days_until_service,
                'is_overdue': days_until_service < 0
            })
    
    # Sort by urgency (overdue first, then by days remaining)
    upcoming_services.sort(key=lambda x: (x['days_until_service'] >= 0, x['days_until_service']))
    
    # Service frequency statistics for last 6 months
    monthly_services = []
    for i in range(6):
        month_start = datetime.utcnow().replace(day=1) - timedelta(days=30*i)
        month_end = month_start.replace(day=28) + timedelta(days=4)  # End of month
        month_end = month_end - timedelta(days=month_end.day)
        
        service_count = ServiceLog.query.filter(
            ServiceLog.service_date >= month_start.date(),
            ServiceLog.service_date <= month_end.date()
        ).count()
        
        monthly_services.append({
            'month': month_start.strftime('%Y-%m'),
            'count': service_count
        })
    
    monthly_services.reverse()
    
    return render_template('dashboard/service.html',
                         stats=stats,
                         recent_services=recent_services,
                         my_recent_services=my_recent_services,
                         upcoming_services=upcoming_services[:10],
                         monthly_services=monthly_services)

@service_bp.route('/dg-sets')
@login_required
@require_service_entry
def dg_sets():
    """View all DG sets for service management"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    search_query = request.args.get('search', '')
    service_status = request.args.get('service_status', '')  # due, overdue, recent
    
    query = DGSetDetail.query.filter_by(is_active=True)
    
    # Apply search filter
    if search_query:
        query = query.filter(
            (DGSetDetail.dg_set_number.contains(search_query)) |
            (DGSetDetail.make.contains(search_query)) |
            (DGSetDetail.model.contains(search_query))
        )
    
    # Apply status filter
    if status_filter:
        from models.dgset import DGSetStatus
        try:
            status_enum = DGSetStatus(status_filter)
            query = query.filter_by(status=status_enum)
        except ValueError:
            pass
    
    dg_sets = query.order_by(DGSetDetail.dg_set_number).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Apply service status filter after pagination
    if service_status and service_status in ['due', 'overdue', 'recent']:
        filtered_items = []
        current_date = datetime.utcnow().date()
        
        for dg_set in dg_sets.items:
            if service_status == 'overdue':
                if dg_set.next_service_due and dg_set.next_service_due < current_date:
                    filtered_items.append(dg_set)
            elif service_status == 'due':
                if (dg_set.next_service_due and 
                    dg_set.next_service_due <= current_date + timedelta(days=30)):
                    filtered_items.append(dg_set)
            elif service_status == 'recent':
                if (dg_set.last_service_date and 
                    dg_set.last_service_date >= current_date - timedelta(days=30)):
                    filtered_items.append(dg_set)
        
        dg_sets.items = filtered_items
    
    from models.dgset import DGSetStatus
    return render_template('dashboard/service_dg_sets.html',
                         dg_sets=dg_sets,
                         status_filter=status_filter,
                         search_query=search_query,
                         service_status=service_status,
                         dg_set_statuses=DGSetStatus)

@service_bp.route('/service-logs')
@login_required
@require_service_entry
def service_logs():
    """View service logs"""
    page = request.args.get('page', 1, type=int)
    dg_set_filter = request.args.get('dg_set', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    service_type = request.args.get('service_type', '')
    
    query = ServiceLog.query
    
    # Apply DG set filter
    if dg_set_filter:
        try:
            dg_set_id = int(dg_set_filter)
            query = query.filter_by(dg_set_id=dg_set_id)
        except ValueError:
            pass
    
    # Apply date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(ServiceLog.service_date >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(ServiceLog.service_date <= to_date)
        except ValueError:
            pass
    
    # Apply service type filter
    if service_type:
        query = query.filter(ServiceLog.service_type.contains(service_type))
    
    service_logs = query.order_by(desc(ServiceLog.service_date)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Get DG sets for filter dropdown
    dg_sets = DGSetDetail.query.filter_by(is_active=True).order_by(
        DGSetDetail.dg_set_number
    ).all()
    
    return render_template('dashboard/service_logs.html',
                         service_logs=service_logs,
                         dg_sets=dg_sets,
                         dg_set_filter=dg_set_filter,
                         date_from=date_from,
                         date_to=date_to,
                         service_type=service_type)

@service_bp.route('/my-services')
@login_required
@require_service_entry
def my_services():
    """View my service logs"""
    page = request.args.get('page', 1, type=int)
    
    service_logs = ServiceLog.query.filter_by(
        created_by=current_user.id
    ).order_by(desc(ServiceLog.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('dashboard/service_my_services.html',
                         service_logs=service_logs)

@service_bp.route('/pin-verification', methods=['GET', 'POST'])
@login_required
@require_service_entry
def pin_verification():
    """PIN verification for service entry"""
    if request.method == 'POST':
        pin = request.form.get('pin', '').strip()
        
        if not pin:
            flash('PIN is required.', 'error')
            return render_template('dashboard/service_pin_verification.html')
        
        # Store PIN in session for service entry
        from flask import session
        session['service_pin'] = pin
        session['service_pin_time'] = datetime.utcnow()
        
        flash('PIN verified. You can now log service entries.', 'success')
        return redirect(url_for('service.dashboard'))
    
    return render_template('dashboard/service_pin_verification.html')