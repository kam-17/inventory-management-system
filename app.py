from flask import Flask
from config import config
from extensions import db, login_manager, mail, csrf
import os

def create_app(config_name=None):
    if config_name is None:
        config_name = os.environ.get('FLASK_CONFIG') or 'default'
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)
    csrf.init_app(app)
    
    # Configure login manager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from models.user import User
        return User.query.get(int(user_id))
    
    # Register blueprints
    from routes.auth.auth import auth_bp
    from routes.dashboard.admin import admin_bp
    from routes.dashboard.office import office_bp
    from routes.dashboard.store import store_bp
    from routes.dashboard.service import service_bp
    from routes.main import main_bp
    
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(office_bp, url_prefix='/office')
    app.register_blueprint(store_bp, url_prefix='/store')
    app.register_blueprint(service_bp, url_prefix='/service')
    app.register_blueprint(main_bp)
    
    # Create database tables
    with app.app_context():
        # Import all models to ensure they are registered
        from models.user import User, OTPLog, AuditLog
        from models.master_data import SiteMaster, SubSite, MaterialCategory, InventoryMaterial  
        from models.inventory import InventoryStock, InventoryMovement
        from models.dgset import DGSetLetter, DGSetDetail, ServiceLog
        from models.delivery_challan import DGDCRegister, DGDCItem
        
        db.create_all()
    
    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)