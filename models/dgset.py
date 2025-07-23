from extensions import db
from datetime import datetime
import enum

class DGSetStatus(enum.Enum):
    AVAILABLE = "AVAILABLE"
    ASSIGNED = "ASSIGNED"
    MAINTENANCE = "MAINTENANCE"
    TRANSFERRED = "TRANSFERRED"
    DECOMMISSIONED = "DECOMMISSIONED"

class DGSetLetter(db.Model):
    __tablename__ = 'dg_set_letters'
    
    id = db.Column(db.Integer, primary_key=True)
    letter = db.Column(db.String(5), unique=True, nullable=False)  # A, B, C, etc.
    description = db.Column(db.String(100))
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    dg_sets = db.relationship('DGSetDetail', backref='letter_ref', lazy='dynamic')
    
    def __repr__(self):
        return f'<DGSetLetter {self.letter}>'

class DGSetDetail(db.Model):
    __tablename__ = 'dg_set_details'
    
    id = db.Column(db.Integer, primary_key=True)
    dg_set_number = db.Column(db.String(50), unique=True, nullable=False)
    letter_id = db.Column(db.Integer, db.ForeignKey('dg_set_letters.id'), nullable=False)
    
    # Basic Information
    make = db.Column(db.String(100), nullable=False)
    model = db.Column(db.String(100), nullable=False)
    rating_kva = db.Column(db.Float, nullable=False)
    rating_kw = db.Column(db.Float, nullable=False)
    frequency = db.Column(db.Float, default=50.0)  # Hz
    voltage = db.Column(db.String(20), default='415V')
    phase = db.Column(db.String(20), default='3-Phase')
    
    # Engine Details
    engine_make = db.Column(db.String(100))
    engine_model = db.Column(db.String(100))
    engine_serial_number = db.Column(db.String(100))
    engine_capacity_cc = db.Column(db.Integer)
    engine_fuel_type = db.Column(db.String(20), default='Diesel')
    
    # Alternator Details
    alternator_make = db.Column(db.String(100))
    alternator_model = db.Column(db.String(100))
    alternator_serial_number = db.Column(db.String(100))
    
    # Status and Location
    status = db.Column(db.Enum(DGSetStatus), default=DGSetStatus.AVAILABLE)
    current_site_id = db.Column(db.Integer, db.ForeignKey('site_master.id'))
    current_sub_site_id = db.Column(db.Integer, db.ForeignKey('sub_sites.id'))
    
    # Maintenance Information
    purchase_date = db.Column(db.Date)
    warranty_expiry = db.Column(db.Date)
    last_service_date = db.Column(db.Date)
    next_service_due = db.Column(db.Date)
    service_hours = db.Column(db.Float, default=0.0)
    
    # Additional Details
    fuel_tank_capacity = db.Column(db.Float)  # Liters
    weight_kg = db.Column(db.Float)
    dimensions = db.Column(db.String(100))  # L x W x H
    remarks = db.Column(db.Text)
    
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    current_site = db.relationship('SiteMaster', backref='dg_sets')
    current_sub_site = db.relationship('SubSite', backref='dg_sets')
    service_logs = db.relationship('ServiceLog', backref='dg_set', lazy='dynamic')
    dc_items = db.relationship('DGDCItem', backref='dg_set', lazy='dynamic')
    
    def get_full_designation(self):
        return f"{self.dg_set_number}{self.letter_ref.letter}"
    
    def get_location_name(self):
        if self.current_sub_site:
            return f"{self.current_site.site_name} - {self.current_sub_site.sub_site_name}"
        elif self.current_site:
            return self.current_site.site_name
        return "Not Assigned"
    
    def is_available_for_assignment(self):
        return self.status == DGSetStatus.AVAILABLE and self.is_active
    
    def __repr__(self):
        return f'<DGSetDetail {self.get_full_designation()} - {self.rating_kva}KVA>'

class ServiceLog(db.Model):
    __tablename__ = 'service_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    dg_set_id = db.Column(db.Integer, db.ForeignKey('dg_set_details.id'), nullable=False)
    service_date = db.Column(db.Date, nullable=False)
    service_type = db.Column(db.String(50), nullable=False)  # ROUTINE, BREAKDOWN, MAJOR, etc.
    
    # Service Details
    technician_name = db.Column(db.String(100))
    service_company = db.Column(db.String(100))
    hours_before_service = db.Column(db.Float)
    hours_after_service = db.Column(db.Float)
    
    # Work Done
    work_description = db.Column(db.Text)
    parts_replaced = db.Column(db.Text)
    oil_changed = db.Column(db.Boolean, default=False)
    filter_changed = db.Column(db.Boolean, default=False)
    
    # Costs
    service_cost = db.Column(db.Float, default=0.0)
    parts_cost = db.Column(db.Float, default=0.0)
    total_cost = db.Column(db.Float, default=0.0)
    
    # Next Service
    next_service_hours = db.Column(db.Float)
    next_service_date = db.Column(db.Date)
    
    remarks = db.Column(db.Text)
    service_pin = db.Column(db.String(10))  # For SERVICE_ENTRY role verification
    
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    creator = db.relationship('User', backref='service_logs')
    
    def calculate_total_cost(self):
        self.total_cost = self.service_cost + self.parts_cost
    
    def __repr__(self):
        return f'<ServiceLog DG:{self.dg_set_id} Date:{self.service_date}>'