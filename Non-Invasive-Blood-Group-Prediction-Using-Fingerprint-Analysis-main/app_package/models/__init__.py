from app_package import db, login_manager
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(UserMixin, db.Model):
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    phone = db.Column(db.String(15))
    blood_group = db.Column(db.String(5), index=True)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    pincode = db.Column(db.String(10), index=True)
    is_donor = db.Column(db.Boolean, default=False, index=True)
    is_admin = db.Column(db.Boolean, default=False)
    date_joined = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    predictions = db.relationship('PredictionHistory', backref='user', lazy=True, cascade='all, delete-orphan')
    emergency_requests = db.relationship('EmergencyRequest', backref='requester', lazy=True, cascade='all, delete-orphan')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'phone': self.phone,
            'blood_group': self.blood_group,
            'city': self.city,
            'pincode': self.pincode,
            'is_donor': self.is_donor,
            'date_joined': self.date_joined.isoformat() if self.date_joined else None
        }

class BloodBank(db.Model):
    __tablename__ = 'blood_bank'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    pincode = db.Column(db.String(10), nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120))
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    available_blood_groups = db.Column(db.Text) 
    is_active = db.Column(db.Boolean, default=True, index=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'pincode': self.pincode,
            'phone': self.phone,
            'email': self.email,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'available_blood_groups': self.available_blood_groups,
            'is_active': self.is_active,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }

class BloodDonor(db.Model):
    __tablename__ = 'blood_donor'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    address = db.Column(db.Text, nullable=False)
    city = db.Column(db.String(100), nullable=False, index=True)
    pincode = db.Column(db.String(10), nullable=False, index=True)
    phone = db.Column(db.String(15), nullable=False)
    email = db.Column(db.String(120))
    blood_group = db.Column(db.String(5), nullable=False, index=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    is_active = db.Column(db.Boolean, default=True, index=True)
    last_updated = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    added_by_user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    
    # Relationship
    added_by = db.relationship('User', backref='added_donors', lazy=True)
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'name': self.name,
            'address': self.address,
            'city': self.city,
            'pincode': self.pincode,
            'phone': self.phone,
            'email': self.email,
            'blood_group': self.blood_group,
            'latitude': self.latitude,
            'longitude': self.longitude,
            'is_active': self.is_active,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'added_by_user_id': self.added_by_user_id
        }

class PredictionHistory(db.Model):
    __tablename__ = 'prediction_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True, index=True)
    session_id = db.Column(db.String(100))
    predicted_blood_group = db.Column(db.String(5), nullable=False, index=True)
    confidence_score = db.Column(db.Float, nullable=False)
    num_fingerprints = db.Column(db.Integer, nullable=False)
    fingerprint_filenames = db.Column(db.Text)  
    prediction_details = db.Column(db.Text) 
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'predicted_blood_group': self.predicted_blood_group,
            'confidence_score': self.confidence_score,
            'num_fingerprints': self.num_fingerprints,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }

class EmergencyRequest(db.Model):
    __tablename__ = 'emergency_request'
    
    id = db.Column(db.Integer, primary_key=True)
    requester_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    blood_group_needed = db.Column(db.String(5), nullable=False, index=True)
    patient_name = db.Column(db.String(100))
    hospital_name = db.Column(db.String(200))
    hospital_address = db.Column(db.Text)
    contact_phone = db.Column(db.String(15), nullable=False)
    urgency_level = db.Column(db.String(20), index=True)  
    units_needed = db.Column(db.Integer, default=1)
    location_pincode = db.Column(db.String(10), index=True)
    status = db.Column(db.String(20), default='Active', index=True) 
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    fulfilled_at = db.Column(db.DateTime)
    # Track successful matches
    donors_found = db.Column(db.Integer, default=0)
    banks_found = db.Column(db.Integer, default=0)
    has_matches = db.Column(db.Boolean, default=False, index=True)
    
    def to_dict(self):
        return {
            'id': self.id,
            'blood_group_needed': self.blood_group_needed,
            'patient_name': self.patient_name,
            'hospital_name': self.hospital_name,
            'urgency_level': self.urgency_level,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'donors_found': self.donors_found,
            'banks_found': self.banks_found,
            'has_matches': self.has_matches
        }