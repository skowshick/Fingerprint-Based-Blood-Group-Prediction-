from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app_package.models import BloodDonor, db
from datetime import datetime

blood_donor_bp = Blueprint('blood_donor', __name__)

@blood_donor_bp.route('/donors')
@login_required
def manage_donors():
    """Blood donor management page"""
    return render_template('blood_donor.html')

@blood_donor_bp.route('/add_donor', methods=['POST'])
@login_required
def add_donor():
    """Add a new blood donor"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate required fields
        required_fields = ['name', 'address', 'city', 'pincode', 'phone', 'blood_group']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create new blood donor
        donor = BloodDonor(
            name=data.get('name'),
            address=data.get('address'),
            city=data.get('city'),
            pincode=data.get('pincode'),
            phone=data.get('phone'),
            email=data.get('email'),
            blood_group=data.get('blood_group'),
            latitude=float(data.get('latitude')) if data.get('latitude') else None,
            longitude=float(data.get('longitude')) if data.get('longitude') else None,
            added_by_user_id=current_user.id
        )
        
        db.session.add(donor)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'donor': donor.to_dict()}), 201
        else:
            flash('Blood donor added successfully!', 'success')
            return redirect(url_for('blood_donor.manage_donors'))
            
    except Exception as e:
        db.session.rollback()
        print(f"Add donor error: {e}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Failed to add donor: {str(e)}', 'error')
            return redirect(url_for('blood_donor.manage_donors'))

@blood_donor_bp.route('/donors/list')
@login_required
def list_donors():
    """Get list of blood donors"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 100, type=int)  # Increased default limit
        blood_group = request.args.get('blood_group', '').strip()
        city = request.args.get('city', '').strip()
        pincode = request.args.get('pincode', '').strip()
        
        print(f"\n🔍 Filtering donors:")
        print(f"   Blood Group: '{blood_group}' (applied: {bool(blood_group)})")
        print(f"   City: '{city}' (applied: {bool(city)})")
        print(f"   Pincode: '{pincode}' (applied: {bool(pincode)})")
        print(f"   Per Page: {per_page}")
        
        query = BloodDonor.query.filter_by(is_active=True)
        
        # Apply filters with case-insensitive matching
        if blood_group:
            query = query.filter(BloodDonor.blood_group == blood_group)
            print(f"   ✓ Filtering by blood group: {blood_group}")
        if city:
            query = query.filter(BloodDonor.city.ilike(f'%{city}%'))
            print(f"   ✓ Filtering by city (contains): {city}")
        if pincode:
            # Use LIKE for partial pincode matching
            query = query.filter(BloodDonor.pincode.like(f'{pincode}%'))
            print(f"   ✓ Filtering by pincode (starts with): {pincode}")
        
        # Paginate results
        donors = query.order_by(BloodDonor.last_updated.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        print(f"   📊 Results: {len(donors.items)} donors found (total: {donors.total})\n")
        
        return jsonify({
            'donors': [donor.to_dict() for donor in donors.items],
            'total': donors.total,
            'pages': donors.pages,
            'current_page': page
        })
        
    except Exception as e:
        print(f"❌ List donors error: {e}")
        return jsonify({'error': str(e)}), 500

@blood_donor_bp.route('/donors/search')
def search_donors():
    """Search for blood donors by pincode and blood group, also return blood banks"""
    try:
        from app_package.models import BloodBank
        import json
        
        blood_group = request.args.get('blood_group')
        pincode = request.args.get('pincode')
        city = request.args.get('city')
        
        if not blood_group and not pincode and not city:
            return jsonify({'error': 'At least one search parameter is required'}), 400
            
        # Base query for donors
        donor_query = BloodDonor.query.filter_by(is_active=True)
        
        # Filter by blood group if provided
        if blood_group:
            donor_query = donor_query.filter(BloodDonor.blood_group == blood_group)
        
        # Filter by pincode or city
        if pincode:
            donor_query = donor_query.filter(BloodDonor.pincode == pincode)
        elif city:
            donor_query = donor_query.filter(BloodDonor.city.ilike(f'%{city}%'))
        
        donors = donor_query.order_by(BloodDonor.last_updated.desc()).limit(50).all()
        
        # Search for blood banks in the same pincode
        blood_banks = []
        if pincode:
            bank_query = BloodBank.query.filter_by(pincode=pincode, is_active=True)
            banks = bank_query.all()
            
            for bank in banks:
                try:
                    available_groups = json.loads(bank.available_blood_groups) if bank.available_blood_groups else {}
                    # If blood group specified, only include banks that have it
                    if not blood_group or (blood_group in available_groups and int(available_groups.get(blood_group, 0)) > 0):
                        bank_dict = bank.to_dict()
                        bank_dict['available_blood_groups'] = available_groups
                        blood_banks.append(bank_dict)
                except (json.JSONDecodeError, ValueError, TypeError):
                    continue
        
        return jsonify({
            'success': True,
            'donors': [donor.to_dict() for donor in donors],
            'blood_banks': blood_banks,
            'donors_count': len(donors),
            'banks_count': len(blood_banks)
        })
        
    except Exception as e:
        print(f"Search donors error: {e}")
        return jsonify({'error': str(e)}), 500

@blood_donor_bp.route('/donors/<int:donor_id>', methods=['PUT'])
@login_required
def update_donor(donor_id):
    """Update blood donor details"""
    try:
        donor = BloodDonor.query.get_or_404(donor_id)
        
        # Check if user can update this donor
        if donor.added_by_user_id != current_user.id and not current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        
        data = request.get_json()
        
        # Update fields
        for field in ['name', 'address', 'city', 'pincode', 'phone', 'email', 'blood_group']:
            if field in data:
                setattr(donor, field, data[field])
            
        donor.last_updated = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'donor': donor.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        print(f"Update donor error: {e}")
        return jsonify({'error': str(e)}), 500

@blood_donor_bp.route('/donors/<int:donor_id>', methods=['DELETE'])
@login_required
def delete_donor(donor_id):
    """Deactivate blood donor"""
    try:
        donor = BloodDonor.query.get_or_404(donor_id)
        
        # Check if user can delete this donor
        if donor.added_by_user_id != current_user.id and not current_user.is_admin:
            return jsonify({'error': 'Unauthorized'}), 403
        
        donor.is_active = False
        donor.last_updated = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Donor deactivated'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete donor error: {e}")
        return jsonify({'error': str(e)}), 500