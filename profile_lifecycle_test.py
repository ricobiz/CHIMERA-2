#!/usr/bin/env python3
"""
Profile Lifecycle Testing - Focused test for review request
Tests profile lifecycle endpoints and behavior per spec.
"""

import requests
import json
import time
import os
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://chimera-auto.preview.emergentagent.com/api"

def log_test(test_name, success, message, details=None):
    """Log test results"""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}: {message}")
    if details and not success:
        print(f"   Details: {details}")
    return success

def test_profile_create():
    """Step 1: Create a profile with region=US"""
    print("\n🧪 Step 1: Creating profile with region=US...")
    
    payload = {"region": "US"}
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/profile/create",
            json=payload,
            timeout=120  # Extended timeout for profile creation
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields per spec
            required_fields = ['profile_id', 'is_warm']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                profile_id = data['profile_id']
                is_warm = data.get('is_warm')
                
                if is_warm == True:
                    log_test(
                        "Profile Create",
                        True,
                        f"Profile created with ID: {profile_id}, is_warm=true"
                    )
                    return profile_id
                else:
                    log_test(
                        "Profile Create - Not Warm",
                        False,
                        f"Profile created but is_warm={is_warm}, expected true"
                    )
                    return None
            else:
                log_test(
                    "Profile Create - Missing Fields",
                    False,
                    f"Response missing required fields: {missing_fields}"
                )
                return None
        else:
            log_test(
                "Profile Create - HTTP Error",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return None
            
    except requests.exceptions.Timeout:
        log_test(
            "Profile Create - Timeout",
            False,
            "Profile creation timed out after 120 seconds"
        )
        return None
    except Exception as e:
        log_test(
            "Profile Create - Exception",
            False,
            f"Unexpected error: {str(e)}"
        )
        return None

def test_profile_use(profile_id):
    """Step 2: Use profile to create session"""
    print(f"\n🧪 Step 2: Using profile {profile_id} to create session...")
    
    payload = {"profile_id": profile_id}
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/profile/use",
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if 'session_id' in data:
                session_id = data['session_id']
                log_test(
                    "Profile Use",
                    True,
                    f"Session created: {session_id}"
                )
                return session_id
            else:
                log_test(
                    "Profile Use - Missing Session ID",
                    False,
                    "Response missing session_id field"
                )
                return None
        else:
            log_test(
                "Profile Use - HTTP Error",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test(
            "Profile Use - Exception",
            False,
            f"Unexpected error: {str(e)}"
        )
        return None

def test_profile_status(profile_id):
    """Step 3: Check profile status"""
    print(f"\n🧪 Step 3: Checking profile {profile_id} status...")
    
    try:
        response = requests.get(
            f"{BACKEND_URL}/profile/{profile_id}/status",
            timeout=15
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check required fields per spec
            required_fields = ['profile_id', 'created_at', 'last_used', 'used_count']
            missing_fields = [field for field in required_fields if field not in data]
            
            if not missing_fields:
                used_count = data.get('used_count', 0)
                
                log_test(
                    "Profile Status",
                    True,
                    f"Status retrieved: used_count={used_count}"
                )
                return data
            else:
                log_test(
                    "Profile Status - Missing Fields",
                    False,
                    f"Response missing required fields: {missing_fields}"
                )
                return None
        else:
            log_test(
                "Profile Status - HTTP Error",
                False,
                f"HTTP {response.status_code}: {response.text}"
            )
            return None
            
    except Exception as e:
        log_test(
            "Profile Status - Exception",
            False,
            f"Unexpected error: {str(e)}"
        )
        return None

def validate_meta_file(profile_id):
    """Validate meta.json file exists and has correct fields"""
    print(f"\n🧪 Validating meta.json file for profile {profile_id}...")
    
    try:
        meta_path = f"/app/runtime/profiles/{profile_id}/meta.json"
        storage_path = f"/app/runtime/profiles/{profile_id}/storage_state.json"
        
        # Check if meta.json exists
        if os.path.exists(meta_path):
            with open(meta_path, 'r') as f:
                meta = json.load(f)
            
            # Check required fields per spec
            checks = []
            
            # Status should be 'warm'
            status = meta.get('status')
            checks.append(('status=warm', status == 'warm', status))
            
            # Warmup should be complete
            warmup = meta.get('warmup', {})
            is_warm = warmup.get('is_warm')
            warmed_at = warmup.get('warmed_at')
            sites_visited = warmup.get('sites_visited', [])
            
            checks.append(('warmup.is_warm=true', is_warm == True, is_warm))
            checks.append(('warmup.warmed_at set', warmed_at is not None, warmed_at))
            checks.append(('sites_visited includes expected sites', 
                          any(site in str(sites_visited) for site in ['google', 'youtube', 'reddit', 'amazon']), 
                          sites_visited))
            
            # Browser info
            browser = meta.get('browser', {})
            user_agent = browser.get('user_agent')
            checks.append(('browser.user_agent present', user_agent is not None and len(user_agent) > 0, bool(user_agent)))
            
            # Locale info
            locale = meta.get('locale', {})
            timezone_id = locale.get('timezone_id')
            locale_str = locale.get('locale')
            languages = locale.get('languages', [])
            
            checks.append(('locale.timezone_id present', timezone_id is not None, timezone_id))
            checks.append(('locale.locale present', locale_str is not None, locale_str))
            checks.append(('locale.languages populated', isinstance(languages, list) and len(languages) > 0, languages))
            
            # Proxy info
            proxy = meta.get('proxy', {})
            proxy_fields = ['ip', 'country', 'region', 'city', 'isp', 'timezone']
            for field in proxy_fields:
                value = proxy.get(field)
                checks.append((f'proxy.{field} present', value is not None, value))
            
            # Check if storage_state.json exists
            storage_exists = os.path.exists(storage_path)
            checks.append(('storage_state.json exists', storage_exists, storage_exists))
            
            # Report results
            failed_checks = [check for check in checks if not check[1]]
            
            if not failed_checks:
                log_test(
                    "Meta File Validation",
                    True,
                    "All required fields present and valid"
                )
                return True
            else:
                failed_descriptions = [f"{check[0]} (got: {check[2]})" for check in failed_checks]
                log_test(
                    "Meta File Validation - Failed Checks",
                    False,
                    f"Failed validations: {'; '.join(failed_descriptions)}"
                )
                return False
        else:
            log_test(
                "Meta File Validation - File Missing",
                False,
                f"Meta.json file not found at {meta_path}"
            )
            return False
            
    except Exception as e:
        log_test(
            "Meta File Validation - Exception",
            False,
            f"Error validating meta file: {str(e)}"
        )
        return False

def test_existing_profile():
    """Test with an existing profile to validate endpoints work"""
    print("\n🧪 Testing with existing profile...")
    
    # Find an existing profile
    profiles_dir = "/app/runtime/profiles"
    if os.path.exists(profiles_dir):
        profiles = [d for d in os.listdir(profiles_dir) if os.path.isdir(os.path.join(profiles_dir, d))]
        if profiles:
            # Use the most recent profile
            profile_id = profiles[-1]
            print(f"   Using existing profile: {profile_id}")
            
            # Test profile use
            session_id = test_profile_use(profile_id)
            
            # Test profile status
            status_data = test_profile_status(profile_id)
            
            return profile_id, session_id, status_data
    
    return None, None, None

def main():
    """Run profile lifecycle tests"""
    print("🚀 Profile Lifecycle Testing - Review Request Specification")
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print("=" * 70)
    
    # Test 1: Test with existing profile first (faster)
    existing_profile_id, session_id, status_data = test_existing_profile()
    
    if existing_profile_id:
        # Validate meta file for existing profile
        validate_meta_file(existing_profile_id)
    
    # Test 2: Create new profile (slower but tests full lifecycle)
    print("\n" + "=" * 70)
    print("🆕 Testing Profile Creation (Full Lifecycle)")
    print("=" * 70)
    
    new_profile_id = test_profile_create()
    
    if new_profile_id:
        # Validate the new profile's meta file
        validate_meta_file(new_profile_id)
        
        # Test using the new profile
        new_session_id = test_profile_use(new_profile_id)
        
        # Test status of the new profile
        new_status_data = test_profile_status(new_profile_id)
    
    print("\n" + "=" * 70)
    print("🏁 Profile Lifecycle Testing Complete")
    print("=" * 70)

if __name__ == "__main__":
    main()