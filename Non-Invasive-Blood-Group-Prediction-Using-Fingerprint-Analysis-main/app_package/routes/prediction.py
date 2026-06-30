from flask import Blueprint, request, jsonify, session, current_app
from flask_login import current_user
from werkzeug.utils import secure_filename
from app_package import db
from app_package.models import PredictionHistory, User
import os
import uuid
import json

# Import prediction functions at module level to avoid delays during requests
try:
    from utils.predict import predict_flexible, calculate_confidence, get_model
    PREDICTION_AVAILABLE = True
    # Preload model when the module is imported to avoid first-request delay
    try:
        get_model()  # This will load the model if not already loaded
        print("Model preloaded successfully!")
    except Exception as e:
        print(f"Warning: Could not preload model: {e}")
except ImportError as e:
    print(f"Warning: Prediction functions not available: {e}")
    PREDICTION_AVAILABLE = False

prediction_bp = Blueprint('prediction', __name__)

@prediction_bp.route('/test', methods=['GET'])
def test():
    """Test endpoint to verify the blueprint is working"""
    return jsonify({'status': 'ok', 'message': 'Prediction routes are working'})

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

@prediction_bp.route('/upload-fingerprints', methods=['POST', 'OPTIONS'])
def upload_fingerprints():
    print(f"=== UPLOAD FINGERPRINTS CALLED === Method: {request.method}")
    
    if request.method == 'OPTIONS':
        print("Handling OPTIONS request")
        return '', 204
    
    try:
        print(f"Request files: {request.files}")
        files = request.files.getlist('fingerprints')
        print(f"Files received: {len(files) if files else 0}")
        
        if not files or len(files) == 0:
            return jsonify({'error': 'No files uploaded'}), 400
        
        max_files = current_app.config.get('MAX_FINGERPRINTS', 10)
        if len(files) > max_files:
            return jsonify({'error': f'Maximum {max_files} fingerprints allowed'}), 400
        
        # Validate files
        for file in files:
            if not allowed_file(file.filename):
                return jsonify({'error': f'Invalid file type: {file.filename}'}), 400
        
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        upload_dir = os.path.join(project_root, current_app.config['UPLOAD_FOLDER'])
        session_files = session.get('uploaded_files', [])
        for old_file in session_files:
            old_path = os.path.join(upload_dir, old_file)
            if os.path.exists(old_path):
                try:
                    os.remove(old_path)
                except:
                    pass
        
        uploaded_files = []
        for file in files:
            if file.filename:
                # Generate unique filename
                unique_filename = f"{uuid.uuid4().hex}_{secure_filename(file.filename)}"
                filepath = os.path.join(upload_dir, unique_filename)
                file.save(filepath)
                uploaded_files.append(unique_filename)
        
        session['uploaded_files'] = uploaded_files
        return jsonify({
            'success': True, 
            'files_count': len(uploaded_files),
            'files': uploaded_files
        })
        
    except Exception as e:
        return jsonify({'error': f'Upload failed: {str(e)}'}), 500

@prediction_bp.route('/predict-blood-group', methods=['POST', 'OPTIONS'])
def predict_blood_group():
    print(f"=== PREDICT BLOOD GROUP CALLED === Method: {request.method}")
    
    if request.method == 'OPTIONS':
        print("Handling OPTIONS request")
        return '', 204
    
    try:
        print(f"Session data: {dict(session)}")
        uploaded_files = session.get('uploaded_files', [])
        print(f"Uploaded files from session: {uploaded_files}")
        if not uploaded_files:
            return jsonify({'error': 'No fingerprints uploaded'}), 400
        
        upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 
                                 current_app.config['UPLOAD_FOLDER'])
        
        # Check if prediction functions are available
        if not PREDICTION_AVAILABLE:
            return jsonify({'error': 'Prediction model not available'}), 500
        
        # Run prediction with quality check
        try:
            print(f"Running prediction on {len(uploaded_files)} files from {upload_dir}")
            predictions = predict_flexible(upload_dir, uploaded_files)
            print(f"Predictions: {predictions}")
        except ValueError as e:
            # Image quality check failed
            print(f"Quality check failed: {e}")
            return jsonify({
                'error': str(e),
                'error_type': 'quality_check_failed'
            }), 400
        except Exception as e:
            print(f"Prediction error: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'Prediction failed: {str(e)}'}), 500
        
        confidence_score = calculate_confidence(predictions)
        
        # Save prediction history
        session_id = session.get('session_id', str(uuid.uuid4()))
        session['session_id'] = session_id
        
        prediction_record = PredictionHistory(
            user_id=current_user.id if current_user.is_authenticated else None,
            session_id=session_id,
            predicted_blood_group=predictions['final_prediction'],
            confidence_score=confidence_score,
            num_fingerprints=len(uploaded_files),
            fingerprint_filenames=json.dumps(uploaded_files),
            prediction_details=json.dumps(predictions)
        )
        
        db.session.add(prediction_record)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'blood_group': predictions['final_prediction'],
            'confidence': confidence_score,
            'num_fingerprints': len(uploaded_files),
            'details': predictions
        })
        
    except Exception as e:
        return jsonify({'error': f'Prediction failed: {str(e)}'}), 500

@prediction_bp.route('/search-donors', methods=['POST'])
def search_donors():
    try:
        data = request.get_json()
        blood_group = data.get('blood_group')
        pincode = data.get('pincode')
        
        if not blood_group or not pincode:
            return jsonify({'error': 'Blood group and pincode are required'}), 400
        
        # Search for donors
        query = User.query.filter_by(is_donor=True, blood_group=blood_group)
        
        # First try exact pincode match
        donors = query.filter_by(pincode=pincode).all()
        
        # If no exact match, search nearby areas
        if not donors:
            pincode_base = pincode[:-1] if len(pincode) > 4 else pincode
            donors = query.filter(User.pincode.like(f"{pincode_base}%")).limit(20).all()
        
        donor_list = []
        for donor in donors:
            donor_list.append({
                'name': donor.username,
                'phone': donor.phone,
                'city': donor.city,
                'pincode': donor.pincode,
                'last_active': donor.last_active.strftime('%Y-%m-%d') if donor.last_active else None
            })
        
        return jsonify({'donors': donor_list})
        
    except Exception as e:
        return jsonify({'error': f'Search failed: {str(e)}'}), 500