#!/usr/bin/env python3
"""
Profile and Hook Exec Gating Testing
Tests new profile management and exec gating functionality
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://aios-automation.preview.emergentagent.com/api"

class ProfileHookTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_profile_id = None
        self.session_id = None
        
    def log_test(self, test_name, success, message, details=None):
        """Log test results"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status} {test_name}: {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    def test_profile_create(self):
        """Test POST /api/profile/create endpoint"""
        print("\n🧪 Testing Profile Creation...")
        
        payload = {
            "region": "US",
            "proxy_tier": "residential"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/profile/create",
                json=payload,
                timeout=60  # Profile creation can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['profile_id', 'is_warm', 'is_clean', 'fingerprint_summary', 'bot_signals']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.created_profile_id = data['profile_id']
                    
                    # Validate field types and values
                    if (isinstance(data['is_warm'], bool) and 
                        isinstance(data['is_clean'], bool) and
                        isinstance(data['fingerprint_summary'], dict) and
                        isinstance(data['bot_signals'], dict)):
                        
                        self.log_test(
                            "Profile Create - Success",
                            True,
                            f"Profile created: {data['profile_id'][:8]}... (warm={data['is_warm']}, clean={data['is_clean']})",
                            {
                                "profile_id": data['profile_id'],
                                "is_warm": data['is_warm'],
                                "is_clean": data['is_clean'],
                                "fingerprint_summary": data['fingerprint_summary'],
                                "bot_signals": data['bot_signals']
                            }
                        )
                    else:
                        self.log_test(
                            "Profile Create - Invalid Field Types",
                            False,
                            "Response fields have incorrect types",
                            {
                                "is_warm_type": type(data.get('is_warm')).__name__,
                                "is_clean_type": type(data.get('is_clean')).__name__,
                                "fingerprint_summary_type": type(data.get('fingerprint_summary')).__name__,
                                "bot_signals_type": type(data.get('bot_signals')).__name__
                            }
                        )
                else:
                    self.log_test(
                        "Profile Create - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Profile Create - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "response_text": response.text}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Profile Create - Timeout",
                False,
                "Profile creation timed out after 60 seconds",
                {"timeout": 60}
            )
        except Exception as e:
            self.log_test(
                "Profile Create - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_profile_status(self):
        """Test GET /api/profile/{profile_id}/status endpoint"""
        print("\n🧪 Testing Profile Status...")
        
        if not self.created_profile_id:
            self.log_test(
                "Profile Status - No Profile ID",
                False,
                "No profile ID available for testing (create profile failed)",
                {"created_profile_id": self.created_profile_id}
            )
            return
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/profile/{self.created_profile_id}/status",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['profile_id', 'region', 'proxy_tier', 'proxy', 'created_at', 
                                 'last_used', 'used_count', 'is_warm', 'is_clean']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test(
                        "Profile Status - Success",
                        True,
                        f"Profile status retrieved: {data['profile_id'][:8]}... (used {data['used_count']} times)",
                        {
                            "profile_id": data['profile_id'],
                            "region": data['region'],
                            "proxy_tier": data['proxy_tier'],
                            "used_count": data['used_count'],
                            "is_warm": data['is_warm'],
                            "is_clean": data['is_clean']
                        }
                    )
                else:
                    self.log_test(
                        "Profile Status - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Profile Status - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Profile Status - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_profile_use(self):
        """Test POST /api/profile/use endpoint"""
        print("\n🧪 Testing Profile Use...")
        
        if not self.created_profile_id:
            self.log_test(
                "Profile Use - No Profile ID",
                False,
                "No profile ID available for testing",
                {"created_profile_id": self.created_profile_id}
            )
            return
        
        payload = {
            "profile_id": self.created_profile_id
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/profile/use",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'session_id' in data:
                    self.session_id = data['session_id']
                    self.log_test(
                        "Profile Use - Success",
                        True,
                        f"Session created: {data['session_id']}",
                        {"session_id": data['session_id']}
                    )
                    
                    # Test screenshot endpoint with the session
                    self.test_automation_screenshot()
                    
                else:
                    self.log_test(
                        "Profile Use - Missing Session ID",
                        False,
                        "Response missing session_id field",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Profile Use - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Profile Use - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_automation_screenshot(self):
        """Test GET /api/automation/screenshot?session_id=... endpoint"""
        print("\n🧪 Testing Automation Screenshot...")
        
        if not self.session_id:
            self.log_test(
                "Automation Screenshot - No Session ID",
                False,
                "No session ID available for testing",
                {"session_id": self.session_id}
            )
            return
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/automation/screenshot/{self.session_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'screenshot_base64' in data and 'vision' in data:
                    screenshot = data['screenshot_base64']
                    vision = data['vision']
                    
                    # Validate screenshot is non-empty base64
                    if screenshot and len(screenshot) > 100:
                        self.log_test(
                            "Automation Screenshot - Success",
                            True,
                            f"Screenshot captured ({len(screenshot)} chars) with {len(vision)} vision elements",
                            {
                                "screenshot_length": len(screenshot),
                                "vision_elements": len(vision),
                                "has_vision": bool(vision)
                            }
                        )
                    else:
                        self.log_test(
                            "Automation Screenshot - Empty Screenshot",
                            False,
                            "Screenshot is empty or too small",
                            {"screenshot_length": len(screenshot) if screenshot else 0}
                        )
                else:
                    self.log_test(
                        "Automation Screenshot - Missing Fields",
                        False,
                        "Response missing screenshot_base64 or vision fields",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Automation Screenshot - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Automation Screenshot - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_profile_check(self):
        """Test POST /api/profile/check endpoint"""
        print("\n🧪 Testing Profile Check...")
        
        if not self.created_profile_id:
            self.log_test(
                "Profile Check - No Profile ID",
                False,
                "No profile ID available for testing",
                {"created_profile_id": self.created_profile_id}
            )
            return
        
        payload = {
            "profile_id": self.created_profile_id
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/profile/check",
                json=payload,
                timeout=45  # Profile checking can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['flashid', 'fingerprint', 'is_clean']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    flashid = data['flashid']
                    fingerprint = data['fingerprint']
                    is_clean = data['is_clean']
                    
                    # Validate screenshots are non-empty base64 strings
                    flashid_screenshot = flashid.get('screenshot_base64', '')
                    fingerprint_screenshot = fingerprint.get('screenshot_base64', '')
                    
                    if (flashid_screenshot and len(flashid_screenshot) > 100 and
                        fingerprint_screenshot and len(fingerprint_screenshot) > 100):
                        
                        self.log_test(
                            "Profile Check - Success",
                            True,
                            f"Profile checked: is_clean={is_clean}, flashid_flagged={flashid.get('flagged_as_bot')}, fingerprint_flagged={fingerprint.get('flagged_as_bot')}",
                            {
                                "is_clean": is_clean,
                                "flashid_flagged": flashid.get('flagged_as_bot'),
                                "fingerprint_flagged": fingerprint.get('flagged_as_bot'),
                                "flashid_screenshot_length": len(flashid_screenshot),
                                "fingerprint_screenshot_length": len(fingerprint_screenshot)
                            }
                        )
                        
                        # Verify meta updated by checking status again
                        self.verify_profile_meta_updated(is_clean)
                        
                    else:
                        self.log_test(
                            "Profile Check - Empty Screenshots",
                            False,
                            "One or both screenshots are empty",
                            {
                                "flashid_screenshot_length": len(flashid_screenshot),
                                "fingerprint_screenshot_length": len(fingerprint_screenshot)
                            }
                        )
                else:
                    self.log_test(
                        "Profile Check - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Profile Check - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Profile Check - Timeout",
                False,
                "Profile check timed out after 45 seconds",
                {"timeout": 45}
            )
        except Exception as e:
            self.log_test(
                "Profile Check - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def verify_profile_meta_updated(self, expected_is_clean):
        """Verify profile meta was updated after check"""
        print("   Verifying profile meta updated...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/profile/{self.created_profile_id}/status",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                actual_is_clean = data.get('is_clean')
                
                if actual_is_clean == expected_is_clean:
                    self.log_test(
                        "Profile Check - Meta Updated",
                        True,
                        f"Profile meta correctly updated: is_clean={actual_is_clean}",
                        {"expected_is_clean": expected_is_clean, "actual_is_clean": actual_is_clean}
                    )
                else:
                    self.log_test(
                        "Profile Check - Meta Not Updated",
                        False,
                        f"Profile meta not updated correctly: expected={expected_is_clean}, actual={actual_is_clean}",
                        {"expected_is_clean": expected_is_clean, "actual_is_clean": actual_is_clean}
                    )
            else:
                self.log_test(
                    "Profile Check - Meta Verification Failed",
                    False,
                    f"Could not verify meta update: HTTP {response.status_code}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Profile Check - Meta Verification Exception",
                False,
                f"Error verifying meta update: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_hook_exec_gating(self):
        """Test POST /api/hook/exec with gating logic"""
        print("\n🧪 Testing Hook Exec Gating...")
        
        payload = {
            "text": "register a new Gmail",
            "timestamp": int(time.time()),
            "nocache": True
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/hook/exec",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get('status') == 'accepted':
                    job_id = data.get('job_id')
                    self.log_test(
                        "Hook Exec - Accepted",
                        True,
                        f"Task accepted with job_id: {job_id}",
                        {"job_id": job_id, "status": data.get('status')}
                    )
                    
                    # Poll for completion or error
                    self.poll_hook_execution(job_id)
                    
                else:
                    self.log_test(
                        "Hook Exec - Not Accepted",
                        False,
                        f"Task not accepted: {data.get('status')}",
                        {"response": data}
                    )
            else:
                self.log_test(
                    "Hook Exec - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Hook Exec - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def poll_hook_execution(self, job_id):
        """Poll /api/hook/log until completion or error"""
        print("   Polling hook execution...")
        
        max_polls = 30  # 30 polls * 2 seconds = 60 seconds max
        poll_count = 0
        
        while poll_count < max_polls:
            try:
                response = self.session.get(
                    f"{BACKEND_URL}/hook/log",
                    params={"nocache": 1},
                    timeout=10
                )
                
                if response.status_code == 200:
                    data = response.json()
                    status = data.get('status')
                    logs = data.get('logs', [])
                    
                    # Check for completion states
                    if status == "ERROR":
                        # Look for bot flagging error
                        error_logs = [log for log in logs if log.get('status') == 'error']
                        if error_logs:
                            last_error = error_logs[-1]
                            error_message = last_error.get('error', '') or last_error.get('action', '')
                            
                            if "Profile flagged as bot" in error_message:
                                self.log_test(
                                    "Hook Exec Gating - Bot Flagged",
                                    True,
                                    "Execution correctly stopped due to bot-flagged profile",
                                    {"error_message": error_message, "status": status}
                                )
                            else:
                                self.log_test(
                                    "Hook Exec Gating - Other Error",
                                    False,
                                    f"Execution failed with different error: {error_message}",
                                    {"error_message": error_message, "status": status}
                                )
                        else:
                            self.log_test(
                                "Hook Exec Gating - Error No Details",
                                False,
                                "Execution failed but no error details found",
                                {"status": status, "logs_count": len(logs)}
                            )
                        return
                    
                    elif status == "DONE":
                        # Check if it proceeded to Gmail signup
                        gmail_logs = [log for log in logs if 'gmail' in log.get('action', '').lower() or 'signup' in log.get('action', '').lower()]
                        if gmail_logs:
                            self.log_test(
                                "Hook Exec Gating - Proceeded to Gmail",
                                True,
                                "Execution proceeded to Gmail signup (profile was clean)",
                                {"gmail_logs_count": len(gmail_logs), "status": status}
                            )
                        else:
                            self.log_test(
                                "Hook Exec Gating - Completed Without Gmail",
                                False,
                                "Execution completed but didn't reach Gmail signup",
                                {"status": status, "logs_count": len(logs)}
                            )
                        return
                    
                    elif status in ["ACTIVE", "WAITING_USER"]:
                        # Still running, continue polling
                        poll_count += 1
                        time.sleep(2)
                        continue
                    
                    else:
                        self.log_test(
                            "Hook Exec Gating - Unknown Status",
                            False,
                            f"Unknown execution status: {status}",
                            {"status": status, "logs_count": len(logs)}
                        )
                        return
                
                else:
                    self.log_test(
                        "Hook Exec Gating - Poll Error",
                        False,
                        f"Polling failed: HTTP {response.status_code}",
                        {"status_code": response.status_code}
                    )
                    return
                    
            except Exception as e:
                self.log_test(
                    "Hook Exec Gating - Poll Exception",
                    False,
                    f"Polling error: {str(e)}",
                    {"error_type": type(e).__name__}
                )
                return
        
        # Timeout
        self.log_test(
            "Hook Exec Gating - Timeout",
            False,
            f"Polling timed out after {max_polls * 2} seconds",
            {"max_polls": max_polls, "timeout_seconds": max_polls * 2}
        )
    
    def test_regression_automation_endpoints(self):
        """Test existing automation endpoints still work"""
        print("\n🧪 Testing Regression - Automation Endpoints...")
        
        if not self.session_id:
            self.log_test(
                "Regression - No Session",
                False,
                "No session available for regression testing",
                {"session_id": self.session_id}
            )
            return
        
        # Test navigation
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/navigate",
                json={"session_id": self.session_id, "url": "https://www.google.com"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'url' in data and 'title' in data:
                    self.log_test(
                        "Regression - Navigation",
                        True,
                        f"Navigation successful: {data.get('title', 'No title')}",
                        {"url": data.get('url'), "title": data.get('title')}
                    )
                else:
                    self.log_test(
                        "Regression - Navigation Missing Fields",
                        False,
                        "Navigation response missing required fields",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Regression - Navigation Error",
                    False,
                    f"Navigation failed: HTTP {response.status_code}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Regression - Navigation Exception",
                False,
                f"Navigation error: {str(e)}",
                {"error_type": type(e).__name__}
            )
        
        # Test click (if elements are available)
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/find-elements",
                json={"session_id": self.session_id, "description": "search button"},
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                elements = data.get('elements', [])
                
                if elements:
                    self.log_test(
                        "Regression - Find Elements",
                        True,
                        f"Found {len(elements)} elements matching 'search button'",
                        {"elements_count": len(elements)}
                    )
                else:
                    self.log_test(
                        "Regression - Find Elements Empty",
                        True,  # Not a failure, just no matching elements
                        "No elements found matching 'search button' (expected on Google homepage)",
                        {"elements_count": 0}
                    )
            else:
                self.log_test(
                    "Regression - Find Elements Error",
                    False,
                    f"Find elements failed: HTTP {response.status_code}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Regression - Find Elements Exception",
                False,
                f"Find elements error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def run_all_tests(self):
        """Run all profile and hook tests"""
        print("🚀 Starting Profile and Hook Exec Gating Tests...")
        print(f"Backend URL: {BACKEND_URL}")
        
        # Profile API Tests
        self.test_profile_create()
        self.test_profile_status()
        self.test_profile_use()
        self.test_profile_check()
        
        # Hook Exec Gating Tests
        self.test_hook_exec_gating()
        
        # Regression Tests
        self.test_regression_automation_endpoints()
        
        # Summary
        self.print_summary()
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "="*80)
        print("📊 TEST SUMMARY")
        print("="*80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        
        print(f"Total Tests: {len(self.test_results)}")
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"  • {result['test']}: {result['message']}")
        
        print("\n✅ PASSED TESTS:")
        for result in self.test_results:
            if result['success']:
                print(f"  • {result['test']}: {result['message']}")

if __name__ == "__main__":
    tester = ProfileHookTester()
    tester.run_all_tests()