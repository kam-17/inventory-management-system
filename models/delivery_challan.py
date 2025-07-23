from extensions import db
from datetime import datetime
import enum

class DCStatus(enum.Enum):
    DRAFT = "DRAFT"
    DISPATCHED = "DISPATCHED"
    PENDING_CLOSE = "PENDING_CLOSE"
    CLOSED = "CLOSED"
    CANCELLED = "CANCELLED"

class ReturnStatus(enum.Enum):
    NOT_APPLICABLE = "NOT_APPLICABLE"
    PENDING = "PENDING"
    PARTIAL = "PARTIAL"
    RETURNED = "RETURNED"

class DGDCRegister(db.Model):
    __tablename__ = 'dg_dc_register'
    
    id = db.Column(db.Integer, primary_key=True)
    dc_number = db.Column(db.String(50), unique=True, nullable=False)
    dc_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.Enum(DCStatus), default=DCStatus.DRAFT)
    
    # Site Information
    site_id = db.Column(db.Integer, db.ForeignKey('site_master.id'), nullable=False)
    sub_site_id = db.Column(db.Integer, db.ForeignKey('sub_sites.id'))
    
    # Transport Information
    vehicle_number = db.Column(db.String(20))
    driver_name = db.Column(db.String(100))
    driver_phone = db.Column(db.String(20))
    transport_company = db.Column(db.String(100))
    
    # DC Type and Purpose
    dc_type = db.Column(db.String(50), default='DELIVERY')  # DELIVERY, TRANSFER, RETURN
    purpose = db.Column(db.String(200))
    priority = db.Column(db.String(20), default='NORMAL')  # URGENT, HIGH, NORMAL, LOW
    
    # Timestamps for workflow
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    dispatched_at = db.Column(db.DateTime)
    pending_close_at = db.Column(db.DateTime)
    closed_at = db.Column(db.DateTime)
    
    # User tracking
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    dispatched_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    closed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    
    # Additional Information
    special_instructions = db.Column(db.Text)
    remarks = db.Column(db.Text)
    
    # Closure Information
    closure_remarks = db.Column(db.Text)
    actual_delivery_date = db.Column(db.Date)
    received_by_name = db.Column(db.String(100))
    received_by_designation = db.Column(db.String(100))
    received_by_phone = db.Column(db.String(20))
    
    # PDF Generation tracking
    pdf_generated = db.Column(db.Boolean, default=False)
    pdf_path = db.Column(db.String(255))
    
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    site = db.relationship('SiteMaster', backref='dcs')
    sub_site = db.relationship('SubSite', backref='dcs')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_dcs')
    dispatcher = db.relationship('User', foreign_keys=[dispatched_by], backref='dispatched_dcs')
    closer = db.relationship('User', foreign_keys=[closed_by], backref='closed_dcs')
    items = db.relationship('DGDCItem', backref='dc', lazy='dynamic', cascade='all, delete-orphan')
    
    def get_dc_display_number(self):
        return f"DC-{self.dc_number}"
    
    def get_total_items(self):
        return self.items.count()
    
    def get_total_quantity(self):
        return sum(item.quantity for item in self.items)
    
    def get_return_summary(self):
        total_items = self.items.count()
        returned_items = self.items.filter_by(return_status=ReturnStatus.RETURNED).count()
        pending_items = self.items.filter(DGDCItem.return_status.in_([ReturnStatus.PENDING, ReturnStatus.PARTIAL])).count()
        
        return {
            'total': total_items,
            'returned': returned_items,
            'pending': pending_items,
            'percentage': (returned_items / total_items * 100) if total_items > 0 else 0
        }
    
    def can_be_dispatched(self):
        return self.status == DCStatus.DRAFT and self.items.count() > 0
    
    def can_be_closed(self):
        return self.status == DCStatus.PENDING_CLOSE
    
    def __repr__(self):
        return f'<DGDCRegister {self.get_dc_display_number()} - {self.status.value}>'

class DGDCItem(db.Model):
    __tablename__ = 'dg_dc_items'
    
    id = db.Column(db.Integer, primary_key=True)
    dc_id = db.Column(db.Integer, db.ForeignKey('dg_dc_register.id'), nullable=False)
    
    # Item can be either Material or DG Set
    material_id = db.Column(db.Integer, db.ForeignKey('inventory_materials.id'))
    dg_set_id = db.Column(db.Integer, db.ForeignKey('dg_set_details.id'))
    
    # Quantity and Return Information
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, default=0.0)
    total_value = db.Column(db.Float, default=0.0)
    
    # Return Management
    return_status = db.Column(db.Enum(ReturnStatus), default=ReturnStatus.NOT_APPLICABLE)
    returnable = db.Column(db.Boolean, default=False)
    expected_return_date = db.Column(db.Date)
    actual_return_date = db.Column(db.Date)
    returned_quantity = db.Column(db.Float, default=0.0)
    
    # Item specific details
    description = db.Column(db.Text)
    serial_numbers = db.Column(db.Text)  # For tracking individual items
    remarks = db.Column(db.Text)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Check constraint to ensure either material_id or dg_set_id is set, but not both
    __table_args__ = (
        db.CheckConstraint(
            '(material_id IS NOT NULL AND dg_set_id IS NULL) OR (material_id IS NULL AND dg_set_id IS NOT NULL)',
            name='check_item_type'
        ),
    )
    
    def get_item_name(self):
        if self.material:
            return self.material.material_name
        elif self.dg_set:
            return f"DG Set {self.dg_set.get_full_designation()}"
        return "Unknown Item"
    
    def get_item_code(self):
        if self.material:
            return self.material.material_code
        elif self.dg_set:
            return self.dg_set.dg_set_number
        return "N/A"
    
    def get_unit_of_measure(self):
        if self.material:
            return self.material.unit_of_measure
        return "SET"
    
    def calculate_total_value(self):
        self.total_value = self.quantity * self.unit_price
    
    def get_pending_return_quantity(self):
        return max(0, self.quantity - self.returned_quantity) if self.returnable else 0
    
    def is_fully_returned(self):
        return self.returnable and self.returned_quantity >= self.quantity
    
    def update_return_status(self):
        if not self.returnable:
            self.return_status = ReturnStatus.NOT_APPLICABLE
        elif self.returned_quantity == 0:
            self.return_status = ReturnStatus.PENDING
        elif self.returned_quantity < self.quantity:
            self.return_status = ReturnStatus.PARTIAL
        else:
            self.return_status = ReturnStatus.RETURNED
            self.actual_return_date = datetime.utcnow().date()
    
    def __repr__(self):
        return f'<DGDCItem DC:{self.dc_id} Item:{self.get_item_name()} Qty:{self.quantity}>'