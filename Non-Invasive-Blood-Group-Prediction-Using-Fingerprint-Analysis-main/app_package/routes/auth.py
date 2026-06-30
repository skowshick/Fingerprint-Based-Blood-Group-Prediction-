from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash
from flask_login import login_user, logout_user, current_user, login_required
from urllib.parse import urlparse
from app_package import db
from app_package.models import User

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """User login"""
    if request.method == 'POST':
        try:
            if request.is_json:
                data = request.get_json()
                email = data.get('email')
                password = data.get('password')
            else:
                email = request.form.get('email')
                password = request.form.get('password')
            
            print(f"Login attempt for email: {email}")  # Debug logging
            
            if not email or not password:
                error_msg = 'Email and password are required'
                print(f"Login failed: {error_msg}")
                if request.is_json:
                    return jsonify({'error': error_msg}), 400
                else:
                    flash(error_msg, 'error')
                    return render_template('login.html')
            
            user = User.query.filter_by(email=email).first()
            print(f"User found: {user is not None}")  # Debug logging
            
            if user:
                print(f"User ID: {user.id}, Username: {user.username}")  # Debug logging
                password_check = user.check_password(password)
                print(f"Password check result: {password_check}")  # Debug logging
                
                if password_check:
                    login_user(user)
                    print(f"User logged in successfully: {user.email}")  # Debug logging
                    
                    next_page = request.args.get('next')
                    # Validate next parameter for security
                    if next_page and urlparse(next_page).netloc == '':
                        redirect_url = next_page
                    else:
                        redirect_url = url_for('main.dashboard')
                        
                    if request.is_json:
                        return jsonify({'success': True, 'redirect': redirect_url})
                    else:
                        flash('Login successful!', 'success')
                        return redirect(redirect_url)
                else:
                    print("Password check failed")  # Debug logging
            else:
                print("User not found")  # Debug logging
            
            # Login failed
            error_msg = 'Invalid email or password'
            if request.is_json:
                return jsonify({'error': error_msg}), 401
            else:
                flash(error_msg, 'error')
                
        except Exception as e:
            print(f"Login error: {e}")  # Debug logging
            error_msg = 'Login failed. Please try again.'
            if request.is_json:
                return jsonify({'error': error_msg}), 500
            else:
                flash(error_msg, 'error')
    
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """User registration"""
    if request.method == 'POST':
        if request.is_json:
            data = request.get_json()
        else:
            data = request.form.to_dict()
        
        # Check if user already exists
        if User.query.filter_by(email=data.get('email')).first():
            if request.is_json:
                return jsonify({'error': 'Email already registered'})
            else:
                flash('Email already registered', 'error')
                return render_template('register.html')
        
        if User.query.filter_by(username=data.get('username')).first():
            if request.is_json:
                return jsonify({'error': 'Username already taken'})
            else:
                flash('Username already taken', 'error')
                return render_template('register.html')
        
        # Create new user
        user = User(
            username=data.get('username'),
            email=data.get('email'),
            phone=data.get('phone'),
            address=data.get('address'),
            city=data.get('city'),
            pincode=data.get('pincode'),
            blood_group=data.get('blood_group'),  # Optional field
            is_donor=data.get('is_donor', False) == 'true' or data.get('is_donor') is True
        )
        user.set_password(data.get('password'))
        
        try:
            db.session.add(user)
            db.session.commit()
            
            login_user(user)
            if request.is_json:
                return jsonify({'success': True, 'redirect': url_for('main.dashboard')})
            else:
                flash('Registration successful!', 'success')
                return redirect(url_for('main.dashboard'))
        
        except Exception as e:
            db.session.rollback()
            print(f"Registration error: {e}")  # Debug logging
            if request.is_json:
                return jsonify({'error': f'Registration failed: {str(e)}'})
            else:
                flash(f'Registration failed: {str(e)}', 'error')
    
    return render_template('register.html')

@auth_bp.route('/logout')
@login_required
def logout():
    """User logout"""
    logout_user()
    flash('You have been logged out.', 'info')
    return redirect(url_for('main.dashboard'))