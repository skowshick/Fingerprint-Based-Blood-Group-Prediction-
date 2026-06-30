"""Email service for sending notifications"""
from flask_mail import Message, Mail
from flask import current_app
from app_package.models import BloodDonor, BloodBank
import json

mail = Mail()

def send_emergency_email_to_donors(emergency_request):
    """Send emergency alert to all blood donors matching the required blood group"""
    try:
        blood_group = emergency_request.blood_group_needed
        
        # Get all active donors with matching blood group
        donors = BloodDonor.query.filter_by(
            blood_group=blood_group,
            is_active=True
        ).all()
        
        # Filter donors who have email addresses
        donor_emails = [donor.email for donor in donors if donor.email and '@' in donor.email]
        
        if not donor_emails:
            print(f"No donors with valid emails found for blood group {blood_group}")
            return 0
        
        # Prepare email content
        subject = f"🚨 URGENT: {emergency_request.urgency_level} Priority Blood Donation Needed - {blood_group}"
        
        body = f"""
Dear Blood Donor,

URGENT BLOOD DONATION REQUEST

We urgently need your help! A patient requires {blood_group} blood donation.

📋 EMERGENCY DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Patient Name: {emergency_request.patient_name or 'Not disclosed'}
Blood Group Needed: {blood_group}
Units Required: {emergency_request.units_needed}
Urgency Level: {emergency_request.urgency_level}

🏥 LOCATION DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hospital: {emergency_request.hospital_name or 'Not specified'}
Address: {emergency_request.hospital_address or 'Not specified'}
Pincode: {emergency_request.location_pincode or 'Not specified'}

📞 CONTACT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Contact Phone: {emergency_request.contact_phone}

⏰ Request Time: {emergency_request.created_at.strftime('%B %d, %Y at %I:%M %p') if emergency_request.created_at else 'Just now'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Your donation can save a life! If you are available and eligible to donate, 
please contact the provided phone number immediately.

Thank you for being a registered blood donor with BloodDonation.

---
This is an automated emergency notification from BloodDonation Emergency Blood Donor System.
You are receiving this email because you are registered as a {blood_group} blood donor.
"""
        
        # Send email to all donors (in batches to avoid overwhelming the server)
        sent_count = 0
        batch_size = 50
        
        for i in range(0, len(donor_emails), batch_size):
            batch = donor_emails[i:i + batch_size]
            
            msg = Message(
                subject=subject,
                recipients=[current_app.config['MAIL_USERNAME']],  # Send to self
                bcc=batch  # Use BCC for privacy
            )
            msg.body = body
            
            try:
                mail.send(msg)
                sent_count += len(batch)
                print(f"Sent emergency email to {len(batch)} donors (batch {i//batch_size + 1})")
            except Exception as e:
                print(f"Error sending email batch: {e}")
        
        return sent_count
        
    except Exception as e:
        print(f"Error in send_emergency_email_to_donors: {e}")
        return 0


def send_emergency_email_to_blood_banks(emergency_request):
    """Send emergency alert to all blood banks"""
    try:
        blood_group = emergency_request.blood_group_needed
        
        # Get all active blood banks
        blood_banks = BloodBank.query.filter_by(is_active=True).all()
        
        # Filter blood banks with valid email addresses
        bank_emails = [bank.email for bank in blood_banks if bank.email and '@' in bank.email]
        
        if not bank_emails:
            print("No blood banks with valid emails found")
            return 0
        
        # Prepare email content for blood banks
        subject = f"🚨 EMERGENCY: Blood Required - {blood_group} ({emergency_request.urgency_level} Priority)"
        
        body = f"""
Dear Blood Bank,

URGENT BLOOD REQUIREMENT ALERT

An emergency blood request has been registered in your area.

📋 EMERGENCY DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Patient Name: {emergency_request.patient_name or 'Not disclosed'}
Blood Group Needed: {blood_group}
Units Required: {emergency_request.units_needed} unit(s)
Urgency Level: ⚠️ {emergency_request.urgency_level} ⚠️

🏥 HOSPITAL INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Hospital Name: {emergency_request.hospital_name or 'Not specified'}
Hospital Address: {emergency_request.hospital_address or 'Not specified'}
Location Pincode: {emergency_request.location_pincode or 'Not specified'}

📞 CONTACT INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Emergency Contact: {emergency_request.contact_phone}

⏰ Request Timestamp: {emergency_request.created_at.strftime('%B %d, %Y at %I:%M %p') if emergency_request.created_at else 'Just now'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

ACTION REQUIRED:
If your blood bank has {blood_group} blood available, please contact the 
emergency number immediately to coordinate the blood supply.

Time is critical in saving this patient's life!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Best Regards,
BloodDonation Emergency System

---
This is an automated emergency notification.
You are receiving this email because you are registered as a blood bank in our system.
"""
        
        # Send email to all blood banks (in batches)
        sent_count = 0
        batch_size = 50
        
        for i in range(0, len(bank_emails), batch_size):
            batch = bank_emails[i:i + batch_size]
            
            msg = Message(
                subject=subject,
                recipients=[current_app.config['MAIL_USERNAME']],  # Send to self
                bcc=batch  # Use BCC for privacy
            )
            msg.body = body
            
            try:
                mail.send(msg)
                sent_count += len(batch)
                print(f"Sent emergency email to {len(batch)} blood banks (batch {i//batch_size + 1})")
            except Exception as e:
                print(f"Error sending email batch to blood banks: {e}")
        
        return sent_count
        
    except Exception as e:
        print(f"Error in send_emergency_email_to_blood_banks: {e}")
        return 0


def send_emergency_notifications(emergency_request):
    """
    Send emergency notifications to LOCAL donors and blood banks only
    
    Args:
        emergency_request: EmergencyRequest model instance
        
    Returns:
        dict: Summary of sent emails
    """
    try:
        print(f"Sending LOCAL emergency notifications for request ID: {emergency_request.id}")
        
        # Get local matches only
        from app_package.routes.emergency import find_local_blood_banks, find_local_donors
        
        local_donors = find_local_donors(
            emergency_request.location_pincode, 
            emergency_request.blood_group_needed
        )
        local_banks = find_local_blood_banks(
            emergency_request.location_pincode, 
            emergency_request.blood_group_needed
        )
        
        # Use consolidated email approach
        success = send_consolidated_emergency_email(emergency_request, local_donors, local_banks)
        
        result = {
            'success': success,
            'donors_notified': len(local_donors) if success else 0,
            'banks_notified': len(local_banks) if success else 0,
            'total_notified': len(local_donors) + len(local_banks) if success else 0,
            'local_only': True
        }
        
        print(f"LOCAL emergency notifications sent: {len(local_donors)} donors, {len(local_banks)} blood banks")
        return result
        
    except Exception as e:
        print(f"Error sending LOCAL emergency notifications: {e}")
        return {
            'success': False,
            'error': str(e),
            'donors_notified': 0,
            'banks_notified': 0,
            'total_notified': 0,
            'local_only': True
        }


def send_consolidated_emergency_email(emergency_request, local_donors, local_banks):
    """Send one consolidated emergency email with all local recipients in CC"""
    try:
        # Collect all email addresses
        donor_emails = [donor.email for donor in local_donors if donor.email and '@' in donor.email]
        bank_emails = [bank.email for bank in local_banks if bank.email and '@' in bank.email]
        all_emails = list(set(donor_emails + bank_emails))  # Remove duplicates
        
        if not all_emails:
            print(f"No valid email addresses found for emergency notification in pincode {emergency_request.location_pincode}")
            return False
        
        # Prepare email content
        subject = f"🚨 LOCAL EMERGENCY: Blood Donation Needed - {emergency_request.blood_group_needed} in Pincode {emergency_request.location_pincode}"
        
        # Create detailed content
        body = f"""
🩸 URGENT LOCAL BLOOD DONATION REQUEST 🩸

THIS IS A LOCAL EMERGENCY IN YOUR AREA (PINCODE: {emergency_request.location_pincode})

📋 PATIENT DETAILS:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Patient Name: {emergency_request.patient_name}
• Blood Group Needed: {emergency_request.blood_group_needed}
• Units Required: {emergency_request.units_needed}
• Urgency Level: ⚠️ {emergency_request.urgency_level} ⚠️

🏥 HOSPITAL INFORMATION:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Hospital: {emergency_request.hospital_name or 'Not specified'}
• Address: {emergency_request.hospital_address or 'Contact for details'}
• Location: Pincode {emergency_request.location_pincode}

📞 EMERGENCY CONTACT:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Contact Number: {emergency_request.contact_phone}
• Request ID: #{emergency_request.id}
• Request Time: {emergency_request.created_at.strftime('%Y-%m-%d %H:%M')}

🔍 LOCAL RESOURCES FOUND:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

• Blood Donors in your pincode: {len(local_donors)}
• Blood Banks in your pincode: {len(local_banks)}

👥 BLOOD DONORS IN PINCODE {emergency_request.location_pincode}:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        
        # Add donor details
        if local_donors:
            for idx, donor in enumerate(local_donors, 1):
                body += f"""
{idx}. {donor.name} (Blood Group: {donor.blood_group})
   📞 Phone: {donor.phone}
   📧 Email: {donor.email}
   📍 Address: {donor.address}
"""
        else:
            body += "\nNo local donors found with matching blood group.\n"
        
        body += f"\n🏥 BLOOD BANKS IN PINCODE {emergency_request.location_pincode}:\n"
        body += "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        # Add blood bank details
        if local_banks:
            for idx, bank in enumerate(local_banks, 1):
                body += f"""
{idx}. {bank.name}
   📞 Phone: {bank.phone}
   📧 Email: {bank.email}
   🩸 Available Groups: {bank.available_blood_groups}
   📍 Address: {bank.address}
"""
        else:
            body += "\nNo local blood banks found with matching blood group.\n"
        
        body += f"""

⚠️ IMMEDIATE ACTION REQUIRED:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

If you can help with this LOCAL emergency request:

🔴 FOR BLOOD DONORS:
   • Contact the emergency number: {emergency_request.contact_phone}
   • Go to the nearest hospital or blood bank
   • Every minute counts!

🔴 FOR BLOOD BANKS:  
   • Check your inventory for {emergency_request.blood_group_needed}
   • Contact the emergency number: {emergency_request.contact_phone}
   • Coordinate immediate blood supply

This is a LOCAL emergency in YOUR pincode ({emergency_request.location_pincode}).
Your immediate help could save a life!

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tamil Nadu Blood Bank Emergency System | Local Alert
Request Time: {emergency_request.created_at.strftime('%Y-%m-%d %H:%M:%S')}

This email was sent to all blood donors and banks in pincode {emergency_request.location_pincode}
with matching blood group {emergency_request.blood_group_needed}.
        """
        
        # Send single email with all recipients in CC
        primary_recipient = all_emails[0]  # First email as TO
        cc_recipients = all_emails[1:] if len(all_emails) > 1 else []  # Rest as CC
        
        msg = Message(
            subject=subject,
            recipients=[primary_recipient],  # Primary recipient
            cc=cc_recipients,  # All others in CC
            body=body
        )
        
        mail.send(msg)
        
        print(f"✅ Consolidated LOCAL emergency email sent to {len(all_emails)} recipients in pincode {emergency_request.location_pincode}")
        print(f"   Primary: {primary_recipient}")
        print(f"   CC: {len(cc_recipients)} recipients")
        print(f"   Donors: {len(local_donors)}, Banks: {len(local_banks)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to send consolidated LOCAL emergency email: {str(e)}")
        return False


# Legacy functions for backward compatibility
def send_emergency_email_to_donors_legacy(emergency_request):
    """Legacy function - sends to ALL donors, not recommended"""
    return send_emergency_email_to_donors(emergency_request)

def send_emergency_email_to_blood_banks_legacy(emergency_request):
    """Legacy function - sends to ALL banks, not recommended"""
    return send_emergency_email_to_blood_banks(emergency_request)
