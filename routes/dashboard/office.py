from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from utils.auth import require_office
from models.delivery_challan import DGDCRegister, DCStatus
from models.master_data import SiteMaster
from sqlalchemy import desc, func
from datetime import datetime, timedelta

office_bp = Blueprint('office', __name__)

@office_bp.route('/dashboard')
@login_required
@require_office
def dashboard():
    """Office dashboard for DC management"""
    
    # Get DC statistics
    stats = {
        'draft_dcs': DGDCRegister.query.filter_by(status=DCStatus.DRAFT).count(),
        'dispatched_dcs': DGDCRegister.query.filter_by(status=DCStatus.DISPATCHED).count(),
        'pending_close_dcs': DGDCRegister.query.filter_by(status=DCStatus.PENDING_CLOSE).count(),
        'closed_today': DGDCRegister.query.filter(
            DGDCRegister.status == DCStatus.CLOSED,
            func.date(DGDCRegister.closed_at) == datetime.utcnow().date()
        ).count(),
        'total_sites': SiteMaster.query.filter_by(is_active=True).count()
    }
    
    # Get recent DCs created by current user
    my_recent_dcs = DGDCRegister.query.filter_by(
        created_by=current_user.id
    ).order_by(desc(DGDCRegister.created_at)).limit(10).all()
    
    # Get DCs pending action
    pending_dcs = DGDCRegister.query.filter(
        DGDCRegister.status.in_([DCStatus.DISPATCHED, DCStatus.PENDING_CLOSE])
    ).order_by(DGDCRegister.created_at).limit(10).all()
    
    # Weekly DC creation trend
    weekly_stats = []
    for i in range(7):
        date = datetime.utcnow().date() - timedelta(days=i)
        count = DGDCRegister.query.filter(
            func.date(DGDCRegister.created_at) == date
        ).count()
        weekly_stats.append({
            'date': date.strftime('%Y-%m-%d'),
            'count': count
        })
    
    weekly_stats.reverse()
    
    return render_template('dashboard/office.html',
                         stats=stats,
                         my_recent_dcs=my_recent_dcs,
                         pending_dcs=pending_dcs,
                         weekly_stats=weekly_stats)

@office_bp.route('/dc-management')
@login_required
@require_office
def dc_management():
    """DC management page"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    site_filter = request.args.get('site', '')
    
    query = DGDCRegister.query
    
    # Apply filters
    if status_filter:
        try:
            status_enum = DCStatus(status_filter)
            query = query.filter_by(status=status_enum)
        except ValueError:
            pass
    
    if site_filter:
        try:
            site_id = int(site_filter)
            query = query.filter_by(site_id=site_id)
        except ValueError:
            pass
    
    # Order by creation date (newest first)
    query = query.order_by(desc(DGDCRegister.created_at))
    
    dcs = query.paginate(page=page, per_page=20, error_out=False)
    
    # Get all sites for filter dropdown
    sites = SiteMaster.query.filter_by(is_active=True).order_by(SiteMaster.site_name).all()
    
    return render_template('dashboard/office_dc_management.html',
                         dcs=dcs,
                         sites=sites,
                         status_filter=status_filter,
                         site_filter=site_filter,
                         dc_statuses=DCStatus)

@office_bp.route('/reports')
@login_required
@require_office
def reports():
    """Office reports page"""
    return render_template('dashboard/office_reports.html')

@office_bp.route('/my-dcs')
@login_required
@require_office
def my_dcs():
    """My created DCs"""
    page = request.args.get('page', 1, type=int)
    status_filter = request.args.get('status', '')
    
    query = DGDCRegister.query.filter_by(created_by=current_user.id)
    
    if status_filter:
        try:
            status_enum = DCStatus(status_filter)
            query = query.filter_by(status=status_enum)
        except ValueError:
            pass
    
    query = query.order_by(desc(DGDCRegister.created_at))
    dcs = query.paginate(page=page, per_page=20, error_out=False)
    
    return render_template('dashboard/office_my_dcs.html',
                         dcs=dcs,
                         status_filter=status_filter,
                         dc_statuses=DCStatus)