from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from utils.auth import require_admin
from models.user import User, UserRole
from models.master_data import SiteMaster, SubSite, MaterialCategory, InventoryMaterial
from models.dgset import DGSetDetail, DGSetLetter
from models.inventory import InventoryStock
from models.delivery_challan import DGDCRegister, DCStatus
from extensions import db
from sqlalchemy import func, desc

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard')
@login_required
@require_admin
def dashboard():
    """Admin dashboard with overview statistics"""
    
    # Get statistics
    stats = {
        'total_users': User.query.filter_by(is_active=True).count(),
        'total_sites': SiteMaster.query.filter_by(is_active=True).count(),
        'total_materials': InventoryMaterial.query.filter_by(is_active=True).count(),
        'total_dg_sets': DGSetDetail.query.filter_by(is_active=True).count(),
        'active_dcs': DGDCRegister.query.filter(
            DGDCRegister.status.in_([DCStatus.DRAFT, DCStatus.DISPATCHED, DCStatus.PENDING_CLOSE])
        ).count(),
        'low_stock_items': 0  # Will calculate below
    }
    
    # Get low stock materials
    low_stock_materials = []
    materials = InventoryMaterial.query.filter_by(is_active=True).all()
    for material in materials:
        current_stock = material.get_current_stock()
        if current_stock <= material.minimum_stock_level:
            low_stock_materials.append({
                'material': material,
                'current_stock': current_stock,
                'min_level': material.minimum_stock_level
            })
    
    stats['low_stock_items'] = len(low_stock_materials)
    
    # Get recent activities (last 10 DCs)
    recent_dcs = DGDCRegister.query.order_by(desc(DGDCRegister.created_at)).limit(10).all()
    
    # Get user distribution by role
    user_roles = db.session.query(
        User.role, func.count(User.id).label('count')
    ).filter_by(is_active=True).group_by(User.role).all()
    
    role_distribution = {role.value: 0 for role in UserRole}
    for role, count in user_roles:
        role_distribution[role.value] = count
    
    return render_template('dashboard/admin.html',
                         stats=stats,
                         low_stock_materials=low_stock_materials[:5],  # Show top 5
                         recent_dcs=recent_dcs,
                         role_distribution=role_distribution)

@admin_bp.route('/users')
@login_required
@require_admin
def users():
    """Manage users"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    users = User.query.order_by(User.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('dashboard/admin_users.html', users=users)

@admin_bp.route('/sites')
@login_required
@require_admin
def sites():
    """Manage sites"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    sites = SiteMaster.query.order_by(SiteMaster.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('dashboard/admin_sites.html', sites=sites)

@admin_bp.route('/materials')
@login_required
@require_admin
def materials():
    """Manage materials"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    materials = InventoryMaterial.query.order_by(InventoryMaterial.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('dashboard/admin_materials.html', materials=materials)

@admin_bp.route('/dgsets')
@login_required
@require_admin
def dgsets():
    """Manage DG sets"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    dgsets = DGSetDetail.query.order_by(DGSetDetail.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )
    
    return render_template('dashboard/admin_dgsets.html', dgsets=dgsets)

@admin_bp.route('/api/dashboard-stats')
@login_required
@require_admin
def api_dashboard_stats():
    """API endpoint for dashboard statistics"""
    
    # Monthly DC creation stats for chart
    monthly_dcs = db.session.query(
        func.date_format(DGDCRegister.created_at, '%Y-%m').label('month'),
        func.count(DGDCRegister.id).label('count')
    ).filter(
        DGDCRegister.created_at >= func.date_sub(func.now(), func.interval(12, 'month'))
    ).group_by('month').order_by('month').all()
    
    # Stock movement stats
    from models.inventory import InventoryMovement, MovementType
    monthly_movements = db.session.query(
        func.date_format(InventoryMovement.created_at, '%Y-%m').label('month'),
        func.count(InventoryMovement.id).label('count'),
        InventoryMovement.movement_type
    ).filter(
        InventoryMovement.created_at >= func.date_sub(func.now(), func.interval(6, 'month'))
    ).group_by('month', InventoryMovement.movement_type).order_by('month').all()
    
    return jsonify({
        'monthly_dcs': [{'month': month, 'count': count} for month, count in monthly_dcs],
        'monthly_movements': [
            {'month': month, 'count': count, 'type': movement_type.value} 
            for month, count, movement_type in monthly_movements
        ]
    })