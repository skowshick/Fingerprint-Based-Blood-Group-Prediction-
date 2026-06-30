from flask import Blueprint, render_template, request, jsonify, current_app
from flask_login import current_user
from app_package import db
from app_package.models import EmergencyRequest, BloodBank, User
from app_package.services.email_service import send_emergency_notifications, send_consolidated_emergency_email
import json

emergency_bp = Blueprint('emergency', __name__)

@emergency_bp.route('/')
def emergency():
    """Emergency page"""
    return render_template('emergency.html')

@emergency_bp.route('/search', methods=['GET'])
def search_resources():
    """Search for blood donors and banks by coordinates or pincode and blood group (coordinates-first)."""
    try:
        from app_package.models import BloodDonor
        import traceback

        # Get search parameters
        pincode = request.args.get('pincode')
        blood_group = request.args.get('blood_group')
        latitude = request.args.get('latitude')
        longitude = request.args.get('longitude')

        print(f"RAW REQUEST ARGS: {dict(request.args)}")

        # Coordinates-first: use coordinate-based search when both latitude and longitude are provided
        if latitude is not None and longitude is not None and latitude != '' and longitude != '':
            print(f"Using coordinates: latitude='{latitude}', longitude='{longitude}'")
            try:
                lat = float(latitude)
                lng = float(longitude)
            except ValueError as ve:
                print(f"Invalid coordinate values: {ve}")
                return jsonify({'error': 'Invalid coordinates'}), 400

            try:
                nearby_banks = find_nearby_blood_banks_by_coords(lat, lng, blood_group)
                nearby_donors = find_nearby_donors_by_coords(lat, lng, blood_group)

                print(f"Coordinate search results: {len(nearby_banks)} banks, {len(nearby_donors)} donors")
                return jsonify({
                    'success': True,
                    'blood_banks': nearby_banks,
                    'donors': nearby_donors,
                    'banks_count': len(nearby_banks),
                    'donors_count': len(nearby_donors),
                    'search_method': 'coordinates'
                })
            except Exception as e:
                print(f"Coordinate search error: {e}")
                traceback.print_exc()
                return jsonify({'error': f'Coordinate search failed: {str(e)}'}), 500

        # If no coordinates provided, require pincode
        if not pincode:
            return jsonify({'error': 'Either coordinates (latitude/longitude) or pincode is required'}), 400

        # Pincode-based fallback
        try:
            nearby_banks = find_nearby_blood_banks(pincode, blood_group)
            nearby_donors = find_nearby_donors(pincode, blood_group)

            print(f"Pincode search results: {len(nearby_banks)} banks, {len(nearby_donors)} donors")
            return jsonify({
                'success': True,
                'blood_banks': nearby_banks,
                'donors': nearby_donors,
                'banks_count': len(nearby_banks),
                'donors_count': len(nearby_donors),
                'search_method': 'pincode'
            })
        except Exception as e:
            print(f"Pincode search error: {e}")
            traceback.print_exc()
            return jsonify({'error': f'Pincode search failed: {str(e)}'}), 500

    except Exception as e:
        import traceback
        print(f"Search resources error: {e}")
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@emergency_bp.route('/create-request', methods=['POST'])
def create_emergency_request():
    """Create emergency blood request"""
    try:
        data = request.get_json()
        
        required_fields = ['blood_group', 'contact_phone', 'patient_name', 'pincode']
        for field in required_fields:
            if not data.get(field):
                return jsonify({'error': f'{field} is required'}), 400
        
        # Create emergency request
        emergency_request = EmergencyRequest(
            requester_id=current_user.id if current_user.is_authenticated else None,
            blood_group_needed=data.get('blood_group'),
            patient_name=data.get('patient_name'),
            hospital_name=data.get('hospital_name'),
            hospital_address=data.get('hospital_address'),
            contact_phone=data.get('contact_phone'),
            urgency_level=data.get('urgency_level', 'High'),
            units_needed=data.get('units_needed', 1),
            location_pincode=data.get('pincode')
        )
        
        db.session.add(emergency_request)
        db.session.flush()  # Get the ID without committing
        
        # Find LOCAL matches only (same pincode + blood group)
        local_banks = find_local_blood_banks(
            data.get('pincode'), 
            data.get('blood_group')
        )
        local_donors = find_local_donors(
            data.get('pincode'), 
            data.get('blood_group')
        )
        
        # Track successful matches
        emergency_request.donors_found = len(local_donors)
        emergency_request.banks_found = len(local_banks)
        emergency_request.has_matches = (len(local_donors) > 0 or len(local_banks) > 0)
        
        db.session.commit()
        
        # Send consolidated email notification in background
        from threading import Thread
        def send_background_notification():
            try:
                with current_app.app_context():
                    send_consolidated_emergency_email(emergency_request, local_donors, local_banks)
            except Exception as e:
                print(f"Background email error: {e}")
        
        # Start background email thread
        Thread(target=send_background_notification).start()
        
        return jsonify({
            'success': True,
            'request_id': emergency_request.id,
            'local_matches': {
                'banks': [bank.to_dict() for bank in local_banks],
                'donors': [donor.to_dict() for donor in local_donors],
                'banks_count': len(local_banks),
                'donors_count': len(local_donors)
            },
            'message': f"Emergency request created! Found {len(local_donors)} local donors and {len(local_banks)} blood banks. Notifications are being sent."
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': f'Failed to create emergency request: {str(e)}'}), 500

def find_local_blood_banks(pincode, blood_group):
    """Find blood banks in the same pincode with matching blood group"""
    if not pincode or not blood_group:
        return []
    
    try:
        banks = BloodBank.query.filter(
            BloodBank.pincode == pincode,
            BloodBank.is_active == True,
            BloodBank.available_blood_groups.contains(blood_group)
        ).all()
        
        return banks
    except Exception as e:
        print(f"Error finding local banks: {e}")
        return []

def find_local_donors(pincode, blood_group):
    """Find blood donors in the same pincode with matching blood group"""
    if not pincode or not blood_group:
        return []
    
    try:
        from app_package.models import BloodDonor
        
        donors = BloodDonor.query.filter(
            BloodDonor.pincode == pincode,
            BloodDonor.blood_group == blood_group,
            BloodDonor.is_active == True
        ).all()
        
        return donors
    except Exception as e:
        print(f"Error finding local donors: {e}")
        return []

def find_nearby_blood_banks(pincode, blood_group):
    """Find nearby blood banks with specified blood group"""
    try:
        if not pincode:
            return []
        
        # Search for blood banks with exact pincode match
        blood_banks = BloodBank.query.filter_by(
            pincode=pincode, is_active=True
        ).all()
        
        # If no exact match, search nearby pincodes (same first 4 digits)
        if not blood_banks and len(pincode) >= 4:
            pincode_base = pincode[:4]
            blood_banks = BloodBank.query.filter(
                BloodBank.pincode.like(f"{pincode_base}%"),
                BloodBank.is_active == True
            ).limit(15).all()
        
        result = []
        for bank in blood_banks:
            try:
                available_groups = json.loads(bank.available_blood_groups) if bank.available_blood_groups else {}
                
                # If blood group specified, check if bank has it
                if not blood_group or (blood_group in available_groups and int(available_groups.get(blood_group, 0)) > 0):
                    result.append({
                        'name': bank.name,
                        'address': bank.address,
                        'phone': bank.phone,
                        'email': bank.email or 'N/A',
                        'city': bank.city,
                        'pincode': bank.pincode,
                        'available_units': available_groups.get(blood_group, 0) if blood_group else None,
                        'all_available_groups': available_groups
                    })
            except (json.JSONDecodeError, ValueError, TypeError) as e:
                print(f"Error parsing blood groups for bank {bank.id}: {e}")
                continue
        
        return result[:8]
        
    except Exception as e:
        print(f"Find nearby blood banks error: {e}")
        return []

def find_nearby_donors(pincode, blood_group):
    """Find nearby donors with specified blood group from BloodDonor table"""
    try:
        from app_package.models import BloodDonor
        
        print(f"Searching for donors: pincode={pincode}, blood_group={blood_group}")
        
        if not pincode:
            return []
        
        # First, let's check if there are any donors at all in the system
        total_donors = BloodDonor.query.filter_by(is_active=True).count()
        print(f"Total active donors in system: {total_donors}")
        
        # Check donors in this exact pincode
        pincode_donors = BloodDonor.query.filter_by(pincode=pincode, is_active=True).count()
        print(f"Active donors in pincode {pincode}: {pincode_donors}")
        
        # Build query for donors
        query = BloodDonor.query.filter_by(
            pincode=pincode,
            is_active=True
        )
        
        # Add blood group filter only if specified
        if blood_group:
            query = query.filter_by(blood_group=blood_group)
            print(f"Filtering by blood group: {blood_group}")
        
        donors = query.all()
        print(f"Exact match donors found: {len(donors)}")
        
        # If no exact pincode match, search nearby pincodes
        if not donors and len(pincode) >= 4:
            pincode_base = pincode[:4]  # Use first 4 digits for broader search
            print(f"Searching broader area with pincode base: {pincode_base}")
            
            query = BloodDonor.query.filter(
                BloodDonor.pincode.like(f"{pincode_base}%"),
                BloodDonor.is_active == True
            )
            
            # Add blood group filter only if specified
            if blood_group:
                query = query.filter_by(blood_group=blood_group)
                
            donors = query.limit(20).all()
            print(f"Broader search found: {len(donors)} donors")
        
        # If still no donors and blood group was specified, try without blood group restriction
        if not donors and blood_group:
            print(f"No donors found with blood group {blood_group}, searching all donors in area...")
            query = BloodDonor.query.filter_by(
                pincode=pincode,
                is_active=True
            )
            donors = query.all()
            print(f"All donors in exact pincode: {len(donors)}")
            
            # Broader search if still no results
            if not donors and len(pincode) >= 4:
                pincode_base = pincode[:4]
                donors = BloodDonor.query.filter(
                    BloodDonor.pincode.like(f"{pincode_base}%"),
                    BloodDonor.is_active == True
                ).limit(20).all()
                print(f"All donors in broader area: {len(donors)}")
        
        result = []
        for donor in donors:
            result.append({
                'name': donor.name,
                'phone': donor.phone,
                'email': donor.email or 'N/A',
                'address': donor.address,
                'city': donor.city,
                'pincode': donor.pincode,
                'blood_group': donor.blood_group,
                'last_updated': donor.last_updated.strftime('%Y-%m-%d') if donor.last_updated else 'Unknown'
            })
        
        print(f"Returning {len(result)} donors")
        return result[:15]  # Return top 15 results
        
    except Exception as e:
        print(f"Find nearby donors error: {e}")
        import traceback
        traceback.print_exc()
        return []

# Helper function to calculate distance between two coordinates
def calculate_distance(lat1, lng1, lat2, lng2):
    """Calculate distance between two coordinates using Haversine formula (in kilometers)"""
    import math
    
    # Convert latitude and longitude from degrees to radians
    lat1_rad = math.radians(lat1)
    lng1_rad = math.radians(lng1)
    lat2_rad = math.radians(lat2)
    lng2_rad = math.radians(lng2)
    
    # Haversine formula
    dlat = lat2_rad - lat1_rad
    dlng = lng2_rad - lng1_rad
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlng/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in kilometers
    r = 6371
    
    return c * r

def find_nearby_donors_by_coords(user_lat, user_lng, blood_group, radius_km=60):
    """Find nearby donors using coordinate-based distance calculation"""
    try:
        from app_package.models import BloodDonor
        
        print(f"Searching for donors by coordinates: lat={user_lat}, lng={user_lng}, blood_group={blood_group}, radius={radius_km}km")
        
        # Get all active donors with coordinates
        query = BloodDonor.query.filter(
            BloodDonor.is_active == True,
            BloodDonor.latitude.isnot(None),
            BloodDonor.longitude.isnot(None)
        )
        
        # Add blood group filter if specified
        if blood_group:
            query = query.filter_by(blood_group=blood_group)
            print(f"Filtering by blood group: {blood_group}")
        
        all_donors = query.all()
        print(f"Found {len(all_donors)} donors with coordinates in database")
        
        # Calculate distances and filter by radius
        nearby_donors = []
        for donor in all_donors:
            try:
                distance = calculate_distance(user_lat, user_lng, donor.latitude, donor.longitude)
                if distance <= radius_km:
                    donor_data = {
                        'name': donor.name,
                        'phone': donor.phone,
                        'email': donor.email or 'N/A',
                        'address': donor.address,
                        'city': donor.city,
                        'pincode': donor.pincode,
                        'blood_group': donor.blood_group,
                        'latitude': donor.latitude,
                        'longitude': donor.longitude,
                        'distance_km': round(distance, 2),
                        'last_updated': donor.last_updated.strftime('%Y-%m-%d') if donor.last_updated else 'Unknown'
                    }
                    nearby_donors.append(donor_data)
            except Exception as e:
                print(f"Error calculating distance for donor {donor.id}: {e}")
                continue
        
        # Sort by distance
        nearby_donors.sort(key=lambda x: x['distance_km'])
        
        print(f"Found {len(nearby_donors)} donors within {radius_km}km")
        return nearby_donors[:20]  # Return top 20 closest
        
    except Exception as e:
        print(f"Find nearby donors by coords error: {e}")
        import traceback
        traceback.print_exc()
        return []

def find_nearby_blood_banks_by_coords(user_lat, user_lng, blood_group, radius_km=60):
    """Find nearby blood banks using coordinate-based distance calculation"""
    try:
        # Get all active blood banks with coordinates
        query = BloodBank.query.filter(
            BloodBank.is_active == True,
            BloodBank.latitude.isnot(None),
            BloodBank.longitude.isnot(None)
        )
        
        all_banks = query.all()
        print(f"Found {len(all_banks)} blood banks with coordinates in database")
        
        # Calculate distances and filter by radius
        nearby_banks = []
        for bank in all_banks:
            try:
                distance = calculate_distance(user_lat, user_lng, bank.latitude, bank.longitude)
                if distance <= radius_km:
                    try:
                        available_groups = json.loads(bank.available_blood_groups) if bank.available_blood_groups else {}
                    except (json.JSONDecodeError, TypeError):
                        available_groups = {}
                    
                    # If blood group specified, check if bank has it
                    if not blood_group or (blood_group in available_groups and int(available_groups.get(blood_group, 0)) > 0):
                        bank_data = {
                            'name': bank.name,
                            'address': bank.address,
                            'phone': bank.phone,
                            'email': bank.email or 'N/A',
                            'city': bank.city,
                            'pincode': bank.pincode,
                            'latitude': bank.latitude,
                            'longitude': bank.longitude,
                            'distance_km': round(distance, 2),
                            'available_units': available_groups.get(blood_group, 0) if blood_group else None,
                            'all_available_groups': available_groups
                        }
                        nearby_banks.append(bank_data)
            except Exception as e:
                print(f"Error calculating distance for bank {bank.id}: {e}")
                continue
        
        # Sort by distance
        nearby_banks.sort(key=lambda x: x['distance_km'])
        
        print(f"Found {len(nearby_banks)} blood banks within {radius_km}km")
        return nearby_banks[:15]  # Return top 15 closest
        
    except Exception as e:
        print(f"Find nearby blood banks by coords error: {e}")
        import traceback
        traceback.print_exc()
        return []