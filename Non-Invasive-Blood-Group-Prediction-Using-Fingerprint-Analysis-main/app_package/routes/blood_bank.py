from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app_package.models import BloodBank, db
from datetime import datetime
import json

blood_bank_bp = Blueprint('blood_bank', __name__)

@blood_bank_bp.route('/blood-banks')
@login_required
def manage_blood_banks():
    """Blood bank management page"""
    return render_template('blood_bank.html')

@blood_bank_bp.route('/dashboard/stats')
@login_required
def get_dashboard_stats():
    """Get dashboard statistics from database"""
    try:
        # Count total blood banks
        total_banks = BloodBank.query.count()
        
        # Count active blood banks
        active_banks = BloodBank.query.filter_by(is_active=True).count()
        
        # Calculate total blood units and critical stock
        total_units = 0
        critical_types = 0
        blood_banks = BloodBank.query.filter_by(is_active=True).all()
        
        for bank in blood_banks:
            if bank.available_blood_groups:
                try:
                    blood_groups = json.loads(bank.available_blood_groups)
                    for blood_type, units in blood_groups.items():
                        total_units += int(units) if units else 0
                        # Consider stock critical if less than 5 units
                        if int(units) < 5:
                            critical_types += 1
                except (json.JSONDecodeError, ValueError):
                    continue
        
        return jsonify({
            'success': True,
            'stats': {
                'total_banks': total_banks,
                'active_banks': active_banks,
                'total_units': total_units,
                'critical_types': critical_types
            }
        })
        
    except Exception as e:
        print(f"Dashboard stats error: {e}")
        return jsonify({'error': str(e)}), 500

@blood_bank_bp.route('/add_blood_bank', methods=['POST'])
@login_required
def add_blood_bank():
    """Add a new blood bank"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate required fields (latitude/longitude are now optional)
        required_fields = ['name', 'address', 'city', 'pincode', 'phone']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Handle available blood groups
        blood_groups_data = {}
        for bg in ['A+', 'A-', 'B+', 'B-', 'AB+', 'AB-', 'O+', 'O-']:
            units = data.get(f'units_{bg.replace("+", "_pos").replace("-", "_neg")}', 0)
            try:
                blood_groups_data[bg] = int(units) if units else 0
            except ValueError:
                blood_groups_data[bg] = 0
        
        # Create new blood bank
        blood_bank = BloodBank(
            name=data.get('name'),
            address=data.get('address'),
            city=data.get('city'),
            pincode=data.get('pincode'),
            phone=data.get('phone'),
            email=data.get('email'),
            latitude=float(data.get('latitude')) if data.get('latitude') else None,
            longitude=float(data.get('longitude')) if data.get('longitude') else None,
            available_blood_groups=json.dumps(blood_groups_data)
        )
        
        db.session.add(blood_bank)
        db.session.commit()
        
        if request.is_json:
            return jsonify({'success': True, 'blood_bank': blood_bank.to_dict()}), 201
        else:
            flash('Blood bank added successfully!', 'success')
            return redirect(url_for('blood_bank.manage_blood_banks'))
            
    except Exception as e:
        db.session.rollback()
        print(f"Add blood bank error: {e}")
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        else:
            flash(f'Failed to add blood bank: {str(e)}', 'error')
            return redirect(url_for('blood_bank.manage_blood_banks'))

@blood_bank_bp.route('/blood_banks/list')
@login_required
def list_blood_banks():
    """Get list of blood banks"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = request.args.get('per_page', 10, type=int)
        city = request.args.get('city')
        pincode = request.args.get('pincode')
        
        query = BloodBank.query.filter_by(is_active=True)
        
        # Apply filters
        if city:
            query = query.filter(BloodBank.city.ilike(f'%{city}%'))
        if pincode:
            query = query.filter(BloodBank.pincode == pincode)
        
        # Paginate results
        blood_banks = query.order_by(BloodBank.last_updated.desc()).paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Add available blood groups to each blood bank
        result_banks = []
        for bank in blood_banks.items:
            bank_dict = bank.to_dict()
            try:
                available_groups = json.loads(bank.available_blood_groups) if bank.available_blood_groups else {}
                bank_dict['available_blood_groups'] = available_groups
            except json.JSONDecodeError:
                bank_dict['available_blood_groups'] = {}
            result_banks.append(bank_dict)
        
        return jsonify({
            'blood_banks': result_banks,
            'total': blood_banks.total,
            'pages': blood_banks.pages,
            'current_page': page
        })
        
    except Exception as e:
        print(f"List blood banks error: {e}")
        return jsonify({'error': str(e)}), 500

@blood_bank_bp.route('/blood_banks/search')
@login_required  
def search_blood_banks():
    """Search for blood banks by location and blood group"""
    try:
        pincode = request.args.get('pincode')
        blood_group = request.args.get('blood_group')
        city = request.args.get('city')
        
        if not pincode and not city:
            return jsonify({'error': 'Pincode or city is required'}), 400
        
        query = BloodBank.query.filter_by(is_active=True)
        
        # Filter by location
        if pincode:
            # First try exact match
            query = query.filter(BloodBank.pincode == pincode)
            blood_banks = query.all()
            
            # If no exact match, try nearby pincodes (same first 4 digits)
            if not blood_banks and len(pincode) >= 4:
                pincode_base = pincode[:4]
                query = BloodBank.query.filter(
                    BloodBank.pincode.like(f"{pincode_base}%"),
                    BloodBank.is_active == True
                )
                blood_banks = query.limit(20).all()
        elif city:
            blood_banks = query.filter(BloodBank.city.ilike(f'%{city}%')).limit(20).all()
        else:
            blood_banks = []
        
        # Filter by blood group availability if specified
        result = []
        for bank in blood_banks:
            try:
                available_groups = json.loads(bank.available_blood_groups) if bank.available_blood_groups else {}
                
                # If blood group specified, only include banks that have it
                if not blood_group or (blood_group in available_groups and int(available_groups.get(blood_group, 0)) > 0):
                    bank_dict = bank.to_dict()
                    bank_dict['available_blood_groups'] = available_groups
                    if blood_group:
                        bank_dict['available_units'] = available_groups.get(blood_group, 0)
                    result.append(bank_dict)
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"Error parsing blood groups for bank {bank.id}: {e}")
                continue
        
        return jsonify({
            'success': True,
            'blood_banks': result,
            'count': len(result)
        })
        
    except Exception as e:
        print(f"Search blood banks error: {e}")
        return jsonify({'error': str(e)}), 500

@blood_bank_bp.route('/blood_banks/<int:bank_id>', methods=['PUT'])
@login_required
def update_blood_bank(bank_id):
    """Update blood bank information"""
    try:
        blood_bank = BloodBank.query.get_or_404(bank_id)
        data = request.get_json()
        
        # Update fields
        for field in ['name', 'address', 'city', 'pincode', 'phone', 'email']:
            if field in data:
                setattr(blood_bank, field, data[field])
        
        if 'latitude' in data:
            blood_bank.latitude = float(data['latitude'])
        if 'longitude' in data:
            blood_bank.longitude = float(data['longitude'])
        
        # Update available blood groups
        if 'available_blood_groups' in data:
            blood_bank.available_blood_groups = json.dumps(data['available_blood_groups'])
        
        blood_bank.last_updated = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'success': True, 'blood_bank': blood_bank.to_dict()})
        
    except Exception as e:
        db.session.rollback()
        print(f"Update blood bank error: {e}")
        return jsonify({'error': str(e)}), 500

@blood_bank_bp.route('/blood_banks/<int:bank_id>', methods=['DELETE'])
@login_required
def delete_blood_bank(bank_id):
    """Delete/deactivate blood bank"""
    try:
        blood_bank = BloodBank.query.get_or_404(bank_id)
        blood_bank.is_active = False
        blood_bank.last_updated = datetime.utcnow()
        
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Blood bank deactivated successfully'})
        
    except Exception as e:
        db.session.rollback()
        print(f"Delete blood bank error: {e}")
        return jsonify({'error': str(e)}), 500