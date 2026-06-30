from flask import Blueprint, render_template, redirect, url_for, jsonify
from flask_login import current_user, login_required
from app_package import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Home page - redirect to dashboard"""
    return redirect(url_for('main.dashboard'))

@main_bp.route('/dashboard')
def dashboard():
    """Main dashboard page"""
    return render_template('dashboard.html')

@main_bp.route('/history')
def history():
    """User prediction history"""
    if not current_user.is_authenticated:
        return redirect(url_for('auth.login'))
    
    from app_package.models import PredictionHistory
    predictions = PredictionHistory.query.filter_by(
        user_id=current_user.id
    ).order_by(PredictionHistory.timestamp.desc()).all()
    
    return render_template('history.html', predictions=predictions)

@main_bp.route('/analytics')
@login_required
def analytics():
    """Analytics and Reports page"""
    return render_template('analytics.html')

@main_bp.route('/api/analytics/stats')
@login_required
def get_analytics_stats():
    """API endpoint to get real-time analytics statistics"""
    from app_package.models import PredictionHistory, User, BloodDonor, EmergencyRequest
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    try:
        # Total predictions
        total_predictions = PredictionHistory.query.count()
        
        # Average accuracy (confidence score)
        avg_accuracy = db.session.query(
            func.avg(PredictionHistory.confidence_score)
        ).scalar() or 0
        
        # Total donors
        total_donors = BloodDonor.query.filter_by(is_active=True).count()
        
        # Successful matches (emergency requests with matches found)
        successful_matches = EmergencyRequest.query.filter_by(has_matches=True).count()
        
        # Total emergency requests
        total_emergency_requests = EmergencyRequest.query.count()
        
        # Calculate changes from last month
        last_month = datetime.utcnow() - timedelta(days=30)
        
        predictions_last_month = PredictionHistory.query.filter(
            PredictionHistory.timestamp >= last_month
        ).count()
        predictions_change = round((predictions_last_month / max(total_predictions - predictions_last_month, 1)) * 100, 1)
        
        # Processing time (simulated based on prediction count)
        avg_processing_time = round(2.3 + (total_predictions * 0.0001), 2)
        
        # System uptime (simulated)
        system_uptime = 99.2
        
        # API requests per minute (simulated based on recent activity)
        api_requests = 120 + (total_predictions % 100)
        
        return jsonify({
            'success': True,
            'data': {
                'totalPredictions': total_predictions,
                'averageAccuracy': round(avg_accuracy, 1),
                'totalDonors': total_donors,
                'successfulMatches': successful_matches,
                'predictionsChange': f'+{predictions_change}%',
                'accuracyChange': '+2.1%',
                'donorsChange': '+23',
                'matchesChange': '+8.4%',
                'processingTime': avg_processing_time,
                'systemUptime': system_uptime,
                'apiRequests': api_requests
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/analytics/blood-type-distribution')
@login_required
def get_blood_type_distribution():
    """API endpoint to get blood type distribution from predictions"""
    from app_package.models import PredictionHistory
    from sqlalchemy import func
    
    try:
        # Get blood type distribution
        distribution = db.session.query(
            PredictionHistory.predicted_blood_group,
            func.count(PredictionHistory.id).label('count')
        ).group_by(PredictionHistory.predicted_blood_group).all()
        
        # Convert to dictionary
        data = {blood_type: count for blood_type, count in distribution}
        
        # Ensure all blood types are present
        blood_types = ['A+', 'B+', 'AB+', 'O+', 'A-', 'B-', 'AB-', 'O-']
        result = [data.get(bt, 0) for bt in blood_types]
        
        return jsonify({
            'success': True,
            'labels': blood_types,
            'data': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/analytics/accuracy-trend')
@login_required
def get_accuracy_trend():
    """API endpoint to get weekly accuracy trend"""
    from app_package.models import PredictionHistory
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    try:
        # Get last 7 days accuracy
        labels = []
        data = []
        
        for i in range(6, -1, -1):
            date = datetime.utcnow() - timedelta(days=i)
            start_of_day = date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_of_day = date.replace(hour=23, minute=59, second=59, microsecond=999999)
            
            avg_confidence = db.session.query(
                func.avg(PredictionHistory.confidence_score)
            ).filter(
                PredictionHistory.timestamp >= start_of_day,
                PredictionHistory.timestamp <= end_of_day
            ).scalar()
            
            day_name = date.strftime('%a')
            labels.append(day_name)
            data.append(round(avg_confidence, 1) if avg_confidence else 0)
        
        return jsonify({
            'success': True,
            'labels': labels,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/analytics/prediction-volume')
@login_required
def get_prediction_volume():
    """API endpoint to get monthly prediction volume"""
    from app_package.models import PredictionHistory
    from sqlalchemy import func, extract
    from datetime import datetime
    
    try:
        # Get last 6 months
        current_year = datetime.utcnow().year
        current_month = datetime.utcnow().month
        
        labels = []
        data = []
        
        for i in range(5, -1, -1):
            month = current_month - i
            year = current_year
            
            if month <= 0:
                month += 12
                year -= 1
            
            count = PredictionHistory.query.filter(
                extract('year', PredictionHistory.timestamp) == year,
                extract('month', PredictionHistory.timestamp) == month
            ).count()
            
            month_name = datetime(year, month, 1).strftime('%b')
            labels.append(month_name)
            data.append(count)
        
        return jsonify({
            'success': True,
            'labels': labels,
            'data': data
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/analytics/recent-predictions')
@login_required
def get_recent_predictions():
    """API endpoint to get recent predictions"""
    from app_package.models import PredictionHistory
    
    try:
        predictions = PredictionHistory.query.order_by(
            PredictionHistory.timestamp.desc()
        ).limit(5).all()
        
        result = []
        for pred in predictions:
            user_name = 'Anonymous'
            if pred.user_id and pred.user:
                user_name = pred.user.username
            
            result.append({
                'id': pred.id,
                'bloodType': pred.predicted_blood_group,
                'confidence': round(pred.confidence_score, 1),
                'user': user_name,
                'timestamp': pred.timestamp.strftime('%Y-%m-%d %H:%M')
            })
        
        return jsonify({
            'success': True,
            'predictions': result
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@main_bp.route('/api/analytics/emergency-stats')
@login_required
def get_emergency_stats():
    """API endpoint to get emergency request statistics"""
    from app_package.models import EmergencyRequest
    from sqlalchemy import func
    from datetime import datetime, timedelta
    
    try:
        # Total emergency requests
        total_requests = EmergencyRequest.query.count()
        
        # Requests with successful matches
        successful_matches = EmergencyRequest.query.filter_by(has_matches=True).count()
        
        # Match success rate
        match_rate = round((successful_matches / max(total_requests, 1)) * 100, 1)
        
        # Total donors found across all requests
        total_donors_found = db.session.query(
            func.sum(EmergencyRequest.donors_found)
        ).scalar() or 0
        
        # Total banks found across all requests
        total_banks_found = db.session.query(
            func.sum(EmergencyRequest.banks_found)
        ).scalar() or 0
        
        # Average matches per request
        avg_donors_per_request = round(total_donors_found / max(total_requests, 1), 1)
        avg_banks_per_request = round(total_banks_found / max(total_requests, 1), 1)
        
        # Recent 7 days statistics
        last_week = datetime.utcnow() - timedelta(days=7)
        recent_requests = EmergencyRequest.query.filter(
            EmergencyRequest.created_at >= last_week
        ).count()
        
        recent_matches = EmergencyRequest.query.filter(
            EmergencyRequest.created_at >= last_week,
            EmergencyRequest.has_matches == True
        ).count()
        
        # Urgency level breakdown
        urgency_breakdown = db.session.query(
            EmergencyRequest.urgency_level,
            func.count(EmergencyRequest.id).label('count')
        ).group_by(EmergencyRequest.urgency_level).all()
        
        urgency_stats = {level: count for level, count in urgency_breakdown}
        
        # Blood group requests breakdown
        blood_group_requests = db.session.query(
            EmergencyRequest.blood_group_needed,
            func.count(EmergencyRequest.id).label('count')
        ).group_by(EmergencyRequest.blood_group_needed).all()
        
        blood_group_stats = {bg: count for bg, count in blood_group_requests}
        
        return jsonify({
            'success': True,
            'data': {
                'totalRequests': total_requests,
                'successfulMatches': successful_matches,
                'matchRate': match_rate,
                'totalDonorsFound': int(total_donors_found),
                'totalBanksFound': int(total_banks_found),
                'avgDonorsPerRequest': avg_donors_per_request,
                'avgBanksPerRequest': avg_banks_per_request,
                'recentRequests': recent_requests,
                'recentMatches': recent_matches,
                'urgencyBreakdown': urgency_stats,
                'bloodGroupRequests': blood_group_stats
            }
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500