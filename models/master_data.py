from extensions import db
from datetime import datetime
import enum

class SiteMaster(db.Model):
    __tablename__ = 'site_master'
    
    id = db.Column(db.Integer, primary_key=True)
    site_code = db.Column(db.String(20), unique=True, nullable=False)
    site_name = db.Column(db.String(100), nullable=False)
    client_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    contact_person = db.Column(db.String(100))
    contact_phone = db.Column(db.String(20))
    contact_email = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sub_sites = db.relationship('SubSite', backref='site', lazy='dynamic')
    
    def __repr__(self):
        return f'<SiteMaster {self.site_code} - {self.site_name}>'

class SubSite(db.Model):
    __tablename__ = 'sub_sites'
    
    id = db.Column(db.Integer, primary_key=True)
    site_id = db.Column(db.Integer, db.ForeignKey('site_master.id'), nullable=False)
    sub_site_code = db.Column(db.String(20), nullable=False)
    sub_site_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Unique constraint on site_id + sub_site_code
    __table_args__ = (db.UniqueConstraint('site_id', 'sub_site_code', name='unique_sub_site_code_per_site'),)
    
    def get_full_code(self):
        return f"{self.site.site_code}-{self.sub_site_code}"
    
    def __repr__(self):
        return f'<SubSite {self.get_full_code()} - {self.sub_site_name}>'

class MaterialCategory(db.Model):
    __tablename__ = 'material_categories'
    
    id = db.Column(db.Integer, primary_key=True)
    category_code = db.Column(db.String(20), unique=True, nullable=False)
    category_name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    materials = db.relationship('InventoryMaterial', backref='category', lazy='dynamic')
    
    def __repr__(self):
        return f'<MaterialCategory {self.category_code} - {self.category_name}>'

class InventoryMaterial(db.Model):
    __tablename__ = 'inventory_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    material_code = db.Column(db.String(50), unique=True, nullable=False)
    material_name = db.Column(db.String(200), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('material_categories.id'), nullable=False)
    description = db.Column(db.Text)
    unit_of_measure = db.Column(db.String(20), nullable=False)  # PCS, KG, LITER, etc.
    hsn_code = db.Column(db.String(20))
    gst_rate = db.Column(db.Float, default=0.0)
    minimum_stock_level = db.Column(db.Integer, default=0)
    maximum_stock_level = db.Column(db.Integer)
    unit_price = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stock_entries = db.relationship('InventoryStock', backref='material', lazy='dynamic')
    movements = db.relationship('InventoryMovement', backref='material', lazy='dynamic')
    dc_items = db.relationship('DGDCItem', backref='material', lazy='dynamic')
    
    def get_current_stock(self):
        from models.inventory import InventoryStock
        stock = InventoryStock.query.filter_by(material_id=self.id).first()
        return stock.current_quantity if stock else 0
    
    def is_low_stock(self):
        return self.get_current_stock() <= self.minimum_stock_level
    
    def __repr__(self):
        return f'<InventoryMaterial {self.material_code} - {self.material_name}>'