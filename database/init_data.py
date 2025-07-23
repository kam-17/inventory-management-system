#!/usr/bin/env python3
"""
Database initialization script for Inventory Management System
Creates sample data for testing and development
"""

import sys
import os
from datetime import datetime, date, timedelta

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from extensions import db
from models.user import User, UserRole
from models.master_data import SiteMaster, SubSite, MaterialCategory, InventoryMaterial
from models.inventory import InventoryStock, InventoryMovement, MovementType
from models.dgset import DGSetLetter, DGSetDetail, DGSetStatus
from models.delivery_challan import DGDCRegister, DGDCItem, DCStatus

def init_database():
    """Initialize database with sample data"""
    app = create_app('development')
    
    with app.app_context():
        # Create all tables
        db.create_all()
        
        # Check if data already exists
        if User.query.first():
            print("Database already initialized with data!")
            return
        
        print("Initializing database with sample data...")
        
        # Create users
        create_users()
        
        # Create sites
        create_sites()
        
        # Create material categories and materials
        create_materials()
        
        # Create DG sets
        create_dg_sets()
        
        # Create some sample inventory data
        create_inventory_data()
        
        # Create some sample DCs
        create_sample_dcs()
        
        print("Database initialization completed!")

def create_users():
    """Create sample users with different roles"""
    users_data = [
        {
            'username': 'superadmin',
            'email': 'superadmin@inventory.com',
            'password': 'admin123',
            'role': UserRole.SUPER_ADMIN,
            'first_name': 'Super',
            'last_name': 'Admin'
        },
        {
            'username': 'admin',
            'email': 'admin@inventory.com',
            'password': 'admin123',
            'role': UserRole.ADMIN,
            'first_name': 'System',
            'last_name': 'Administrator'
        },
        {
            'username': 'office',
            'email': 'office@inventory.com',
            'password': 'office123',
            'role': UserRole.OFFICE,
            'first_name': 'Office',
            'last_name': 'User'
        },
        {
            'username': 'store',
            'email': 'store@inventory.com',
            'password': 'store123',
            'role': UserRole.STORE,
            'first_name': 'Store',
            'last_name': 'Keeper'
        },
        {
            'username': 'service',
            'email': 'service@inventory.com',
            'password': 'service123',
            'role': UserRole.SERVICE_ENTRY,
            'first_name': 'Service',
            'last_name': 'Engineer'
        }
    ]
    
    for user_data in users_data:
        user = User(
            username=user_data['username'],
            email=user_data['email'],
            role=user_data['role'],
            first_name=user_data['first_name'],
            last_name=user_data['last_name']
        )
        user.set_password(user_data['password'])
        db.session.add(user)
    
    db.session.commit()
    print("Created sample users")

def create_sites():
    """Create sample sites and sub-sites"""
    sites_data = [
        {
            'site_code': 'SITE001',
            'site_name': 'Mumbai Industrial Park',
            'client_name': 'Industrial Corp Ltd',
            'address': 'Plot 123, Industrial Area, Mumbai - 400001',
            'contact_person': 'Rajesh Sharma',
            'contact_phone': '+91-9876543210',
            'contact_email': 'rajesh@industrial.com',
            'sub_sites': [
                {'code': 'A1', 'name': 'Main Building'},
                {'code': 'A2', 'name': 'Warehouse 1'},
                {'code': 'A3', 'name': 'Warehouse 2'}
            ]
        },
        {
            'site_code': 'SITE002',
            'site_name': 'Delhi Corporate Center',
            'client_name': 'Corporate Solutions Pvt Ltd',
            'address': 'Sector 15, Noida, Delhi NCR - 201301',
            'contact_person': 'Priya Singh',
            'contact_phone': '+91-9876543211',
            'contact_email': 'priya@corporate.com',
            'sub_sites': [
                {'code': 'B1', 'name': 'Tower A'},
                {'code': 'B2', 'name': 'Tower B'}
            ]
        },
        {
            'site_code': 'SITE003',
            'site_name': 'Bangalore Tech Hub',
            'client_name': 'Tech Solutions India',
            'address': 'Electronic City, Bangalore - 560100',
            'contact_person': 'Arun Kumar',
            'contact_phone': '+91-9876543212',
            'contact_email': 'arun@techsolutions.com',
            'sub_sites': [
                {'code': 'C1', 'name': 'Development Center'},
                {'code': 'C2', 'name': 'Data Center'}
            ]
        }
    ]
    
    for site_data in sites_data:
        site = SiteMaster(
            site_code=site_data['site_code'],
            site_name=site_data['site_name'],
            client_name=site_data['client_name'],
            address=site_data['address'],
            contact_person=site_data['contact_person'],
            contact_phone=site_data['contact_phone'],
            contact_email=site_data['contact_email']
        )
        db.session.add(site)
        db.session.flush()  # Get the ID
        
        # Add sub-sites
        for sub_site_data in site_data['sub_sites']:
            sub_site = SubSite(
                site_id=site.id,
                sub_site_code=sub_site_data['code'],
                sub_site_name=sub_site_data['name']
            )
            db.session.add(sub_site)
    
    db.session.commit()
    print("Created sample sites and sub-sites")

def create_materials():
    """Create material categories and materials"""
    categories_data = [
        {'code': 'ELECT', 'name': 'Electrical Items'},
        {'code': 'MECH', 'name': 'Mechanical Items'},
        {'code': 'TOOLS', 'name': 'Tools & Equipment'},
        {'code': 'SPARE', 'name': 'Spare Parts'},
        {'code': 'FUEL', 'name': 'Fuel & Lubricants'},
        {'code': 'SAFETY', 'name': 'Safety Equipment'}
    ]
    
    for cat_data in categories_data:
        category = MaterialCategory(
            category_code=cat_data['code'],
            category_name=cat_data['name']
        )
        db.session.add(category)
    
    db.session.commit()
    
    # Get created categories
    elect_cat = MaterialCategory.query.filter_by(category_code='ELECT').first()
    mech_cat = MaterialCategory.query.filter_by(category_code='MECH').first()
    tools_cat = MaterialCategory.query.filter_by(category_code='TOOLS').first()
    spare_cat = MaterialCategory.query.filter_by(category_code='SPARE').first()
    fuel_cat = MaterialCategory.query.filter_by(category_code='FUEL').first()
    safety_cat = MaterialCategory.query.filter_by(category_code='SAFETY').first()
    
    materials_data = [
        # Electrical Items
        {'code': 'CABLE-PVC-3C-2.5', 'name': 'PVC Cable 3 Core 2.5 sq mm', 'category': elect_cat, 'unit': 'MTR', 'price': 45.0, 'min_stock': 100},
        {'code': 'CABLE-PVC-3C-4', 'name': 'PVC Cable 3 Core 4 sq mm', 'category': elect_cat, 'unit': 'MTR', 'price': 72.0, 'min_stock': 50},
        {'code': 'MCB-32A-SP', 'name': 'MCB 32A Single Pole', 'category': elect_cat, 'unit': 'PCS', 'price': 250.0, 'min_stock': 20},
        {'code': 'MCB-63A-TP', 'name': 'MCB 63A Triple Pole', 'category': elect_cat, 'unit': 'PCS', 'price': 850.0, 'min_stock': 10},
        
        # Mechanical Items
        {'code': 'BOLT-M12-50', 'name': 'Hex Bolt M12 x 50mm', 'category': mech_cat, 'unit': 'PCS', 'price': 15.0, 'min_stock': 200},
        {'code': 'NUT-M12', 'name': 'Hex Nut M12', 'category': mech_cat, 'unit': 'PCS', 'price': 5.0, 'min_stock': 500},
        {'code': 'WASHER-M12', 'name': 'Flat Washer M12', 'category': mech_cat, 'unit': 'PCS', 'price': 2.0, 'min_stock': 1000},
        
        # Tools
        {'code': 'DRILL-13MM', 'name': 'Electric Drill 13mm', 'category': tools_cat, 'unit': 'PCS', 'price': 3500.0, 'min_stock': 2},
        {'code': 'HAMMER-500G', 'name': 'Claw Hammer 500g', 'category': tools_cat, 'unit': 'PCS', 'price': 450.0, 'min_stock': 5},
        {'code': 'SPANNER-SET', 'name': 'Combination Spanner Set', 'category': tools_cat, 'unit': 'SET', 'price': 1200.0, 'min_stock': 3},
        
        # Spare Parts
        {'code': 'FILTER-OIL-GEN', 'name': 'Oil Filter for Generator', 'category': spare_cat, 'unit': 'PCS', 'price': 450.0, 'min_stock': 10},
        {'code': 'FILTER-AIR-GEN', 'name': 'Air Filter for Generator', 'category': spare_cat, 'unit': 'PCS', 'price': 650.0, 'min_stock': 8},
        {'code': 'PLUG-SPARK', 'name': 'Spark Plug', 'category': spare_cat, 'unit': 'PCS', 'price': 180.0, 'min_stock': 20},
        
        # Fuel & Lubricants
        {'code': 'DIESEL', 'name': 'Diesel Fuel', 'category': fuel_cat, 'unit': 'LITER', 'price': 95.0, 'min_stock': 500},
        {'code': 'OIL-ENGINE-15W40', 'name': 'Engine Oil 15W40', 'category': fuel_cat, 'unit': 'LITER', 'price': 420.0, 'min_stock': 50},
        {'code': 'GREASE-MULTI', 'name': 'Multi-purpose Grease', 'category': fuel_cat, 'unit': 'KG', 'price': 350.0, 'min_stock': 20},
        
        # Safety Equipment
        {'code': 'HELMET-SAFETY', 'name': 'Safety Helmet', 'category': safety_cat, 'unit': 'PCS', 'price': 250.0, 'min_stock': 20},
        {'code': 'GLOVES-LEATHER', 'name': 'Leather Work Gloves', 'category': safety_cat, 'unit': 'PAIR', 'price': 180.0, 'min_stock': 50},
        {'code': 'BOOTS-SAFETY', 'name': 'Safety Boots', 'category': safety_cat, 'unit': 'PAIR', 'price': 1200.0, 'min_stock': 10}
    ]
    
    for mat_data in materials_data:
        material = InventoryMaterial(
            material_code=mat_data['code'],
            material_name=mat_data['name'],
            category_id=mat_data['category'].id,
            unit_of_measure=mat_data['unit'],
            unit_price=mat_data['price'],
            minimum_stock_level=mat_data['min_stock']
        )
        db.session.add(material)
    
    db.session.commit()
    print("Created material categories and materials")

def create_dg_sets():
    """Create DG set letters and sample DG sets"""
    # Create letters
    letters = ['A', 'B', 'C', 'D', 'E']
    for letter in letters:
        dg_letter = DGSetLetter(letter=letter)
        db.session.add(dg_letter)
    
    db.session.commit()
    
    # Get sites for assignment
    sites = SiteMaster.query.all()
    letter_a = DGSetLetter.query.filter_by(letter='A').first()
    letter_b = DGSetLetter.query.filter_by(letter='B').first()
    letter_c = DGSetLetter.query.filter_by(letter='C').first()
    
    dg_sets_data = [
        {
            'number': '001', 'letter': letter_a, 'make': 'Kirloskar', 'model': 'KG1-62.5AS',
            'kva': 62.5, 'kw': 50, 'site': sites[0] if sites else None,
            'engine_make': 'Kirloskar', 'engine_model': 'HA394'
        },
        {
            'number': '002', 'letter': letter_a, 'make': 'Mahindra', 'model': 'MPG75',
            'kva': 75, 'kw': 60, 'site': sites[1] if len(sites) > 1 else None,
            'engine_make': 'Mahindra', 'engine_model': '2545TC'
        },
        {
            'number': '003', 'letter': letter_b, 'make': 'Cummins', 'model': 'C100D5P',
            'kva': 100, 'kw': 80, 'site': sites[0] if sites else None,
            'engine_make': 'Cummins', 'engine_model': '4BTA3.9-G2'
        },
        {
            'number': '004', 'letter': letter_b, 'make': 'Ashok Leyland', 'model': 'AL125',
            'kva': 125, 'kw': 100, 'site': sites[2] if len(sites) > 2 else None,
            'engine_make': 'Ashok Leyland', 'engine_model': 'H4BF'
        },
        {
            'number': '005', 'letter': letter_c, 'make': 'Greaves', 'model': 'GC-82.5',
            'kva': 82.5, 'kw': 66, 'site': None,  # Available
            'engine_make': 'Greaves', 'engine_model': 'GRT4'
        }
    ]
    
    for dg_data in dg_sets_data:
        dg_set = DGSetDetail(
            dg_set_number=dg_data['number'],
            letter_id=dg_data['letter'].id,
            make=dg_data['make'],
            model=dg_data['model'],
            rating_kva=dg_data['kva'],
            rating_kw=dg_data['kw'],
            engine_make=dg_data['engine_make'],
            engine_model=dg_data['engine_model'],
            current_site_id=dg_data['site'].id if dg_data['site'] else None,
            status=DGSetStatus.ASSIGNED if dg_data['site'] else DGSetStatus.AVAILABLE
        )
        db.session.add(dg_set)
    
    db.session.commit()
    print("Created DG set letters and sample DG sets")

def create_inventory_data():
    """Create initial inventory stock data"""
    materials = InventoryMaterial.query.all()
    
    for material in materials:
        # Create initial stock (3-5 times minimum stock level)
        initial_stock = material.minimum_stock_level * (3 + (material.id % 3))
        
        stock = InventoryStock(
            material_id=material.id,
            current_quantity=initial_stock,
            available_quantity=initial_stock
        )
        db.session.add(stock)
        
        # Create initial inward movement
        movement = InventoryMovement(
            material_id=material.id,
            movement_type=MovementType.INWARD,
            quantity=initial_stock,
            unit_price=material.unit_price,
            total_value=initial_stock * material.unit_price,
            reference_type='INITIAL_STOCK',
            reference_number='INIT-001',
            remarks='Initial stock entry',
            stock_before=0,
            stock_after=initial_stock,
            created_by=1  # Admin user
        )
        db.session.add(movement)
    
    db.session.commit()
    print("Created initial inventory stock data")

def create_sample_dcs():
    """Create some sample delivery challans"""
    sites = SiteMaster.query.all()
    materials = InventoryMaterial.query.limit(5).all()
    
    if not sites or not materials:
        return
    
    # Create a draft DC
    dc1 = DGDCRegister(
        dc_number='DC20240001',
        dc_date=date.today(),
        status=DCStatus.DRAFT,
        site_id=sites[0].id,
        vehicle_number='MH-01-AB-1234',
        driver_name='Ramesh Kumar',
        driver_phone='+91-9876543213',
        purpose='Regular maintenance supplies',
        created_by=3  # Office user
    )
    db.session.add(dc1)
    db.session.flush()
    
    # Add items to DC
    for i, material in enumerate(materials[:3]):
        item = DGDCItem(
            dc_id=dc1.id,
            material_id=material.id,
            quantity=10 + i * 5,
            unit_price=material.unit_price,
            returnable=True if i % 2 == 0 else False
        )
        item.calculate_total_value()
        db.session.add(item)
    
    # Create a dispatched DC
    dc2 = DGDCRegister(
        dc_number='DC20240002',
        dc_date=date.today() - timedelta(days=2),
        status=DCStatus.DISPATCHED,
        site_id=sites[1].id if len(sites) > 1 else sites[0].id,
        vehicle_number='MH-02-CD-5678',
        driver_name='Suresh Patil',
        driver_phone='+91-9876543214',
        purpose='Emergency repair materials',
        created_by=3,  # Office user
        dispatched_by=4,  # Store user
        dispatched_at=datetime.now() - timedelta(days=1)
    )
    db.session.add(dc2)
    db.session.flush()
    
    # Add items to second DC
    for i, material in enumerate(materials[2:]):
        item = DGDCItem(
            dc_id=dc2.id,
            material_id=material.id,
            quantity=5 + i * 3,
            unit_price=material.unit_price,
            returnable=True
        )
        item.calculate_total_value()
        db.session.add(item)
    
    db.session.commit()
    print("Created sample delivery challans")

if __name__ == '__main__':
    init_database()