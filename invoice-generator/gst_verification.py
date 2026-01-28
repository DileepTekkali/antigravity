"""
GST Verification Module
Validates GST numbers and optionally verifies them via API
"""
import re
import requests
from typing import Dict, Tuple

def validate_gst_format(gst_number: str) -> bool:
    """
    Validate GST number format
    Format: 2 digits (state code) + 10 chars (PAN) + 1 char (entity number) + Z + 1 check digit
    Example: 29ABCDE1234F1Z5
    """
    if not gst_number:
        return False
    
    gst_number = gst_number.strip().upper()
    
    # GST should be 15 characters
    if len(gst_number) != 15:
        return False
    
    # Pattern: 2 digits + 10 alphanumeric (PAN format) + 1 digit + Z + 1 alphanumeric
    pattern = r'^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$'
    
    return bool(re.match(pattern, gst_number))

def verify_gst_online(gst_number: str, api_key: str = None) -> Tuple[bool, Dict]:
    """
    Verify GST number online using API
    Returns: (is_valid, details_dict)
    
    Note: This is a placeholder. You'll need to integrate with actual GST API
    Popular options:
    - GST API by MasterIndia
    - GST Verification API by various providers
    """
    if not validate_gst_format(gst_number):
        return False, {'error': 'Invalid GST format'}
    
    # Placeholder for API integration
    # In production, you would call the actual GST verification API here
    
    # Example API call structure (commented out):
    # try:
    #     response = requests.post(
    #         'https://api.gstverification.com/verify',
    #         json={'gst_number': gst_number},
    #         headers={'Authorization': f'Bearer {api_key}'},
    #         timeout=10
    #     )
    #     if response.status_code == 200:
    #         data = response.json()
    #         return data.get('valid', False), data
    #     else:
    #         return False, {'error': 'API error'}
    # except Exception as e:
    #     return False, {'error': str(e)}
    
    # For now, return format validation result
    return True, {
        'valid': True,
        'gst_number': gst_number,
        'message': 'Format validated (online verification not configured)',
        'verified_online': False
    }

def verify_gst(gst_number: str, use_api: bool = False, api_key: str = None) -> Dict:
    """
    Main GST verification function
    Returns a dictionary with verification results
    """
    if not gst_number:
        return {
            'valid': False,
            'error': 'GST number is required',
            'verified_online': False
        }
    
    gst_number = gst_number.strip().upper()
    
    # First check format
    if not validate_gst_format(gst_number):
        return {
            'valid': False,
            'error': 'Invalid GST format. Should be 15 characters (e.g., 29ABCDE1234F1Z5)',
            'verified_online': False
        }
    
    # If API verification is requested
    if use_api and api_key:
        is_valid, details = verify_gst_online(gst_number, api_key)
        return {
            'valid': is_valid,
            'gst_number': gst_number,
            'details': details,
            'verified_online': True
        }
    
    # Return format validation only
    return {
        'valid': True,
        'gst_number': gst_number,
        'message': 'GST format is valid',
        'verified_online': False
    }

def extract_state_code(gst_number: str) -> str:
    """Extract state code from GST number"""
    if validate_gst_format(gst_number):
        return gst_number[:2]
    return None

def extract_pan(gst_number: str) -> str:
    """Extract PAN from GST number"""
    if validate_gst_format(gst_number):
        return gst_number[2:12]
    return None

# State codes mapping (for reference)
STATE_CODES = {
    '01': 'Jammu and Kashmir', '02': 'Himachal Pradesh', '03': 'Punjab',
    '04': 'Chandigarh', '05': 'Uttarakhand', '06': 'Haryana',
    '07': 'Delhi', '08': 'Rajasthan', '09': 'Uttar Pradesh',
    '10': 'Bihar', '11': 'Sikkim', '12': 'Arunachal Pradesh',
    '13': 'Nagaland', '14': 'Manipur', '15': 'Mizoram',
    '16': 'Tripura', '17': 'Meghalaya', '18': 'Assam',
    '19': 'West Bengal', '20': 'Jharkhand', '21': 'Odisha',
    '22': 'Chhattisgarh', '23': 'Madhya Pradesh', '24': 'Gujarat',
    '26': 'Dadra and Nagar Haveli and Daman and Diu', '27': 'Maharashtra',
    '29': 'Karnataka', '30': 'Goa', '31': 'Lakshadweep',
    '32': 'Kerala', '33': 'Tamil Nadu', '34': 'Puducherry',
    '35': 'Andaman and Nicobar Islands', '36': 'Telangana',
    '37': 'Andhra Pradesh', '38': 'Ladakh'
}

def get_state_name(gst_number: str) -> str:
    """Get state name from GST number"""
    state_code = extract_state_code(gst_number)
    return STATE_CODES.get(state_code, 'Unknown')
