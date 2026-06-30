from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from config.config import config
import os

db = SQLAlchemy()
login_manager = LoginManager()

def create_app(config_name=None):
    """Application factory function"""
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    # Get the parent directory (project root) for templates and static files
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    template_dir = os.path.join(project_root, 'templates')
    static_dir = os.path.join(project_root, 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir)
    app.config.from_object(config[config_name])
    
    # Ensure session configuration is set
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'
    
    # Initialize Flask-Mail
    from app_package.services.email_service import mail
    mail.init_app(app)
    
    # User loader function for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        from app_package.models import User
        return User.query.get(int(user_id))
    
    # Create upload directory if it doesn't exist
    upload_dir = os.path.join(project_root, app.config['UPLOAD_FOLDER'])
    os.makedirs(upload_dir, exist_ok=True)
    
    # Register blueprints
    from app_package.routes.main import main_bp
    from app_package.routes.auth import auth_bp
    from app_package.routes.prediction import prediction_bp
    from app_package.routes.emergency import emergency_bp
    from app_package.routes.admin import admin_bp
    from app_package.routes.blood_donor import blood_donor_bp
    from app_package.routes.blood_bank import blood_bank_bp
    
    app.register_blueprint(main_bp)
    app.register_blueprint(auth_bp)  # No prefix for auth routes
    app.register_blueprint(prediction_bp, url_prefix='/predict')
    app.register_blueprint(emergency_bp, url_prefix='/emergency')
    app.register_blueprint(admin_bp, url_prefix='/admin')
    app.register_blueprint(blood_donor_bp, url_prefix='/blood_donor')
    app.register_blueprint(blood_bank_bp, url_prefix='/blood-bank')
    
    # Add CORS headers to all responses
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
        response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
        return response
    
    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return {'error': 'Page not found'}, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return {'error': 'Internal server error'}, 500
    
    return app