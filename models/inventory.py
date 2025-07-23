from extensions import db
from datetime import datetime
import enum

class MovementType(enum.Enum):
    INWARD = "INWARD"
    OUTWARD = "OUTWARD"

class InventoryStock(db.Model):
    __tablename__ = 'inventory_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('inventory_materials.id'), nullable=False)
    current_quantity = db.Column(db.Float, default=0.0)
    reserved_quantity = db.Column(db.Float, default=0.0)  # Reserved for pending DCs
    available_quantity = db.Column(db.Float, default=0.0)  # current - reserved
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint - one stock record per material
    __table_args__ = (db.UniqueConstraint('material_id', name='unique_material_stock'),)
    
    def update_available_quantity(self):
        self.available_quantity = self.current_quantity - self.reserved_quantity
        self.last_updated = datetime.utcnow()
    
    def add_stock(self, quantity):
        self.current_quantity += quantity
        self.update_available_quantity()
    
    def remove_stock(self, quantity):
        if self.available_quantity >= quantity:
            self.current_quantity -= quantity
            self.update_available_quantity()
            return True
        return False
    
    def reserve_stock(self, quantity):
        if self.available_quantity >= quantity:
            self.reserved_quantity += quantity
            self.update_available_quantity()
            return True
        return False
    
    def release_stock(self, quantity):
        if self.reserved_quantity >= quantity:
            self.reserved_quantity -= quantity
            self.update_available_quantity()
            return True
        return False
    
    def __repr__(self):
        return f'<InventoryStock Material:{self.material_id} Current:{self.current_quantity}>'

class InventoryMovement(db.Model):
    __tablename__ = 'inventory_movement'
    
    id = db.Column(db.Integer, primary_key=True)
    material_id = db.Column(db.Integer, db.ForeignKey('inventory_materials.id'), nullable=False)
    movement_type = db.Column(db.Enum(MovementType), nullable=False)
    quantity = db.Column(db.Float, nullable=False)
    unit_price = db.Column(db.Float, default=0.0)
    total_value = db.Column(db.Float, default=0.0)
    reference_type = db.Column(db.String(50))  # DC, PURCHASE, ADJUSTMENT, etc.
    reference_id = db.Column(db.Integer)
    reference_number = db.Column(db.String(100))
    remarks = db.Column(db.Text)
    
    # Purchase related fields (for INWARD movements)
    supplier_name = db.Column(db.String(200))
    invoice_number = db.Column(db.String(100))
    invoice_date = db.Column(db.Date)
    gst_amount = db.Column(db.Float, default=0.0)
    
    # Stock levels after this movement
    stock_before = db.Column(db.Float)
    stock_after = db.Column(db.Float)
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='inventory_movements')
    
    def calculate_total_value(self):
        self.total_value = self.quantity * self.unit_price
    
    def __repr__(self):
        return f'<InventoryMovement {self.movement_type.value} {self.quantity} of Material:{self.material_id}>'