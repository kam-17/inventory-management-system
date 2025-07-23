from flask import Blueprint, render_template, request
from flask_login import login_required, current_user
from utils.auth import require_store
from models.inventory import InventoryStock, InventoryMovement, MovementType
from models.master_data import InventoryMaterial, MaterialCategory
from models.delivery_challan import DGDCRegister, DCStatus
from extensions import db
from sqlalchemy import desc, func
from datetime import datetime, timedelta

store_bp = Blueprint('store', __name__)

@store_bp.route('/dashboard')
@login_required
@require_store
def dashboard():
    """Store dashboard for inventory management"""
    
    # Get inventory statistics
    stats = {
        'total_materials': InventoryMaterial.query.filter_by(is_active=True).count(),
        'low_stock_items': 0,  # Will calculate below
        'total_stock_value': 0.0,
        'pending_dispatches': DGDCRegister.query.filter_by(status=DCStatus.DRAFT).count(),
        'pending_returns': DGDCRegister.query.filter_by(status=DCStatus.PENDING_CLOSE).count()
    }
    
    # Calculate low stock items and total value
    low_stock_materials = []
    total_value = 0.0
    
    materials = InventoryMaterial.query.filter_by(is_active=True).all()
    for material in materials:
        current_stock = material.get_current_stock()
        if current_stock <= material.minimum_stock_level:
            low_stock_materials.append({
                'material': material,
                'current_stock': current_stock,
                'min_level': material.minimum_stock_level
            })
        
        total_value += current_stock * material.unit_price
    
    stats['low_stock_items'] = len(low_stock_materials)
    stats['total_stock_value'] = total_value
    
    # Get recent inventory movements
    recent_movements = InventoryMovement.query.order_by(
        desc(InventoryMovement.created_at)
    ).limit(10).all()
    
    # Get stock movement summary for last 7 days
    weekly_movements = []
    for i in range(7):
        date = datetime.utcnow().date() - timedelta(days=i)
        
        inward = db.session.query(func.sum(InventoryMovement.quantity)).filter(
            func.date(InventoryMovement.created_at) == date,
            InventoryMovement.movement_type == MovementType.INWARD
        ).scalar() or 0
        
        outward = db.session.query(func.sum(InventoryMovement.quantity)).filter(
            func.date(InventoryMovement.created_at) == date,
            InventoryMovement.movement_type == MovementType.OUTWARD
        ).scalar() or 0
        
        weekly_movements.append({
            'date': date.strftime('%Y-%m-%d'),
            'inward': float(inward),
            'outward': float(outward)
        })
    
    weekly_movements.reverse()
    
    # Get category-wise stock distribution
    category_stats = db.session.query(
        MaterialCategory.category_name,
        func.count(InventoryMaterial.id).label('material_count'),
        func.sum(InventoryStock.current_quantity * InventoryMaterial.unit_price).label('total_value')
    ).join(
        InventoryMaterial, MaterialCategory.id == InventoryMaterial.category_id
    ).outerjoin(
        InventoryStock, InventoryMaterial.id == InventoryStock.material_id
    ).filter(
        InventoryMaterial.is_active == True
    ).group_by(MaterialCategory.id, MaterialCategory.category_name).all()
    
    return render_template('dashboard/store.html',
                         stats=stats,
                         low_stock_materials=low_stock_materials[:5],
                         recent_movements=recent_movements,
                         weekly_movements=weekly_movements,
                         category_stats=category_stats)

@store_bp.route('/inventory')
@login_required
@require_store
def inventory():
    """Inventory management page"""
    page = request.args.get('page', 1, type=int)
    category_filter = request.args.get('category', '')
    search_query = request.args.get('search', '')
    stock_filter = request.args.get('stock_status', '')  # low, normal, out_of_stock
    
    query = InventoryMaterial.query.filter_by(is_active=True)
    
    # Apply search filter
    if search_query:
        query = query.filter(
            (InventoryMaterial.material_name.contains(search_query)) |
            (InventoryMaterial.material_code.contains(search_query))
        )
    
    # Apply category filter
    if category_filter:
        try:
            category_id = int(category_filter)
            query = query.filter_by(category_id=category_id)
        except ValueError:
            pass
    
    # Get materials with stock information
    materials = query.order_by(InventoryMaterial.material_name).paginate(
        page=page, per_page=20, error_out=False
    )
    
    # Apply stock status filter after pagination (for simplicity)
    if stock_filter and stock_filter in ['low', 'out_of_stock']:
        filtered_items = []
        for material in materials.items:
            current_stock = material.get_current_stock()
            if stock_filter == 'out_of_stock' and current_stock == 0:
                filtered_items.append(material)
            elif stock_filter == 'low' and 0 < current_stock <= material.minimum_stock_level:
                filtered_items.append(material)
            elif stock_filter == 'normal' and current_stock > material.minimum_stock_level:
                filtered_items.append(material)
        materials.items = filtered_items
    
    # Get all categories for filter dropdown
    categories = MaterialCategory.query.filter_by(is_active=True).order_by(
        MaterialCategory.category_name
    ).all()
    
    return render_template('dashboard/store_inventory.html',
                         materials=materials,
                         categories=categories,
                         category_filter=category_filter,
                         search_query=search_query,
                         stock_filter=stock_filter)

@store_bp.route('/movements')
@login_required
@require_store
def movements():
    """Inventory movements page"""
    page = request.args.get('page', 1, type=int)
    movement_type = request.args.get('type', '')
    date_from = request.args.get('date_from', '')
    date_to = request.args.get('date_to', '')
    
    query = InventoryMovement.query
    
    # Apply movement type filter
    if movement_type:
        try:
            movement_enum = MovementType(movement_type)
            query = query.filter_by(movement_type=movement_enum)
        except ValueError:
            pass
    
    # Apply date filters
    if date_from:
        try:
            from_date = datetime.strptime(date_from, '%Y-%m-%d').date()
            query = query.filter(func.date(InventoryMovement.created_at) >= from_date)
        except ValueError:
            pass
    
    if date_to:
        try:
            to_date = datetime.strptime(date_to, '%Y-%m-%d').date()
            query = query.filter(func.date(InventoryMovement.created_at) <= to_date)
        except ValueError:
            pass
    
    movements = query.order_by(desc(InventoryMovement.created_at)).paginate(
        page=page, per_page=20, error_out=False
    )
    
    return render_template('dashboard/store_movements.html',
                         movements=movements,
                         movement_type=movement_type,
                         date_from=date_from,
                         date_to=date_to,
                         movement_types=MovementType)

@store_bp.route('/dispatch')
@login_required
@require_store
def dispatch():
    """DC dispatch management"""
    page = request.args.get('page', 1, type=int)
    
    # Get DCs ready for dispatch (DRAFT status)
    dcs = DGDCRegister.query.filter_by(status=DCStatus.DRAFT).order_by(
        DGDCRegister.created_at
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('dashboard/store_dispatch.html', dcs=dcs)

@store_bp.route('/returns')
@login_required
@require_store
def returns():
    """Manage returns from DCs"""
    page = request.args.get('page', 1, type=int)
    
    # Get DCs pending closure (items may need to be returned)
    dcs = DGDCRegister.query.filter_by(status=DCStatus.PENDING_CLOSE).order_by(
        DGDCRegister.pending_close_at
    ).paginate(page=page, per_page=20, error_out=False)
    
    return render_template('dashboard/store_returns.html', dcs=dcs)