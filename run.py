import os
# Suppress TensorFlow warnings early
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '2'
os.environ['TF_ENABLE_ONEDNN_OPTS'] = '0'

from app_package import create_app, db
from app_package.models import User, BloodBank, PredictionHistory, EmergencyRequest
from flask.cli import with_appcontext
from sqlalchemy import text, inspect
import click

def check_column_exists(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        inspector = inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except:
        return False

def run_migrations():
    """Run necessary database migrations"""
    try:
        # Check if emergency_request table exists
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'emergency_request' not in tables:
            return True  # Table will be created by db.create_all()
        
        # Check if columns already exist
        needs_donors_found = not check_column_exists('emergency_request', 'donors_found')
        needs_banks_found = not check_column_exists('emergency_request', 'banks_found')
        needs_has_matches = not check_column_exists('emergency_request', 'has_matches')
        
        if not (needs_donors_found or needs_banks_found or needs_has_matches):
            return True  # No migration needed
        
        print("\n" + "="*60)
        print("🔄 Running database migrations...")
        print("="*60)
        
        # Add donors_found column
        if needs_donors_found:
            print("  Adding column: donors_found...")
            db.session.execute(text(
                "ALTER TABLE emergency_request ADD COLUMN donors_found INTEGER DEFAULT 0"
            ))
            db.session.commit()
            print("  ✓ Added donors_found")
        
        # Add banks_found column
        if needs_banks_found:
            print("  Adding column: banks_found...")
            db.session.execute(text(
                "ALTER TABLE emergency_request ADD COLUMN banks_found INTEGER DEFAULT 0"
            ))
            db.session.commit()
            print("  ✓ Added banks_found")
        
        # Add has_matches column
        if needs_has_matches:
            print("  Adding column: has_matches...")
            db.session.execute(text(
                "ALTER TABLE emergency_request ADD COLUMN has_matches BOOLEAN DEFAULT 0"
            ))
            db.session.commit()
            print("  ✓ Added has_matches")
            
            # Try to create index
            try:
                db.session.execute(text(
                    "CREATE INDEX idx_emergency_request_has_matches ON emergency_request(has_matches)"
                ))
                db.session.commit()
                print("  ✓ Created index on has_matches")
            except:
                db.session.rollback()
        
        print("="*60)
        print("✅ Migrations completed successfully!")
        print("="*60 + "\n")
        return True
        
    except Exception as e:
        db.session.rollback()
        return True  # Continue anyway

def create_database_tables(app):
    with app.app_context():
        try:
            db.engine.connect()
            
            db.create_all()
            
            run_migrations()
            
            admin = User.query.filter_by(email='admin@bloodsystem.com').first()
            if not admin:
                admin = User(
                    username='admin',
                    email='admin@bloodsystem.com',
                    phone='+1234567890',
                    is_admin=True,
                    city='Emergency City',
                    pincode='12345',
                    blood_group='O+',
                    is_donor=True
                )
                admin.set_password('admin123')
                
                db.session.add(admin)
                db.session.commit()
            else:
                print("✓ Admin user already exists")
                
        except Exception as e:
            return False
    
    return True

def main():
    config_name = os.environ.get('FLASK_ENV', 'development')
    
    app = create_app(config_name)
    
    if not create_database_tables(app):
        return
    
    # Preload ML model during startup for better performance
    print("\n" + "="*60)
    print("🤖 PRELOADING MACHINE LEARNING MODEL")
    print("="*60)
    try:
        from utils.predict import get_model
        print("Loading TensorFlow model...")
        model = get_model()
        print(f"✅ Model loaded successfully! Shape: {model.input_shape if hasattr(model, 'input_shape') else 'N/A'}")
    except Exception as e:
        print(f"⚠️  Warning: Could not preload model: {e}")
        print("Model will be loaded on first prediction request.")
    print("="*60)
    
    @app.cli.command()
    @click.option('--drop', is_flag=True, help='Drop all tables before creating')
    def init_db(drop):
        if drop:
            db.drop_all()
            print("Dropped all tables.")
        
        db.create_all()
        print("Initialized the database.")
    
    @app.cli.command()
    def migrate():
        """Run database migrations"""
        print("\n" + "="*60)
        print("🔄 MANUAL DATABASE MIGRATION")
        print("="*60)
        success = run_migrations()
        if success:
            print("\n✅ Migration completed!")
        else:
            print("\n❌ Migration failed!")
    
    @app.cli.command()
    def create_admin():
        admin = User.query.filter_by(email='admin@bloodsystem.com').first()
        if admin:
            print("Admin user already exists!")
            return
        
        admin = User(
            username='admin',
            email='admin@bloodsystem.com',
            phone='+1234567890',
            is_admin=True,
            city='Emergency City',
            pincode='12345',
            blood_group='O+',
            is_donor=True
        )
        admin.set_password('admin123')
        
        db.session.add(admin)
        db.session.commit()
        print("Admin user created successfully!")
    
    # Run the application
    print("\n" + "="*60)
    print("🩸 BLOOD PREDICTION SYSTEM")
    print("="*60)
    print(f"Environment: {config_name}")
    print(f"Debug Mode: {app.config['DEBUG']}")
    print(f"Database: {app.config['SQLALCHEMY_DATABASE_URI']}")
    print("="*60)
    print("🚀 Starting server...")
    print("📱 Access the app at: http://localhost:5000")
    print("👤 Admin login: admin@bloodsystem.com / admin123")
    print("="*60)
    
    # Run the Flask development server with reloader disabled to avoid TensorFlow file watching issues
    app.run(
        host='0.0.0.0',
        port=5000,
        debug=app.config['DEBUG'],
        threaded=True,
        use_reloader=False  # Disable reloader to prevent crashes from TensorFlow file changes
    )

if __name__ == '__main__':
    main()