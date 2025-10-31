#!/usr/bin/env python3
"""
JustFans.uno Registration Automation Test
Tests complete automation flow for justfans.uno registration using automation APIs directly (bypassing head_brain)

Test Scenario:
1. Create session
2. Navigate to https://justfans.uno/register
3. Fill form with sequential typing in 4 textboxes
4. Click REGISTER button
5. Verify final URL changed or success
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://chimera-auto.preview.emergentagent.com/api"

class JustFansRegistrationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.session_id = "test-registration-final"
        
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
    
    def test_justfans_registration_flow(self):
        """Test complete JustFans.uno registration automation flow"""
        print("\n🎯 Testing JustFans.uno Registration Automation Flow...")
        print("=" * 80)
        
        # STEP 1: Create automation session
        print("\n📋 STEP 1: Create automation session")
        if not self.create_automation_session():
            return False
        
        # STEP 2: Navigate to registration page
        print("\n📋 STEP 2: Navigate to registration page")
        if not self.navigate_to_registration():
            return False
        
        # Wait 3 seconds as specified
        time.sleep(3)
        
        # STEP 3: Get scene to find textbox positions
        print("\n📋 STEP 3: Get scene snapshot to find textbox positions")
        textbox_elements = self.get_scene_textboxes()
        if not textbox_elements:
            return False
        
        # STEP 4-7: Fill form fields sequentially
        print("\n📋 STEP 4-7: Fill form fields sequentially")
        if not self.fill_registration_form(textbox_elements):
            return False
        
        # STEP 8: Click REGISTER button
        print("\n📋 STEP 8: Click REGISTER button")
        if not self.click_register_button():
            return False
        
        # Wait 5 seconds as specified
        time.sleep(5)
        
        # STEP 9: Verify result
        print("\n📋 STEP 9: Verify registration result")
        return self.verify_registration_result()
    
    def create_automation_session(self):
        """STEP 1: Create automation session"""
        payload = {
            "session_id": self.session_id,
            "use_proxy": False
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/session/create",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if data.get("status") == "ready":
                    self.log_test(
                        "Create Session - Success",
                        True,
                        f"Session created with status: {data['status']}",
                        {"session_id": self.session_id, "status": data["status"]}
                    )
                    return True
                else:
                    self.log_test(
                        "Create Session - Wrong Status",
                        False,
                        f"Expected status 'ready', got '{data.get('status')}'",
                        {"expected": "ready", "actual": data.get("status")}
                    )
                    return False
            else:
                self.log_test(
                    "Create Session - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Create Session - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return False
    
    def navigate_to_registration(self):
        """STEP 2: Navigate to registration page"""
        payload = {
            "session_id": self.session_id,
            "url": "https://justfans.uno/register"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/navigate",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                current_url = data.get("url", "")
                if "register" in current_url.lower():
                    self.log_test(
                        "Navigate to Registration - Success",
                        True,
                        f"Successfully navigated to: {current_url}",
                        {"url": current_url}
                    )
                    return True
                else:
                    self.log_test(
                        "Navigate to Registration - Wrong URL",
                        False,
                        f"URL doesn't contain 'register': {current_url}",
                        {"expected_contains": "register", "actual_url": current_url}
                    )
                    return False
            else:
                self.log_test(
                    "Navigate to Registration - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Navigate to Registration - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return False
    
    def get_scene_textboxes(self):
        """STEP 3: Get scene snapshot and find textbox elements"""
        payload = {
            "session_id": self.session_id
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/scene/snapshot",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                elements = data.get("scene", {}).get("elements", [])
                if not elements:
                    elements = data.get("elements", [])
                
                # Find textbox/input elements
                textbox_elements = []
                for element in elements:
                    role = element.get("role", "").lower()
                    
                    # Look for textbox elements
                    if role == "textbox":
                        textbox_elements.append(element)
                
                if len(textbox_elements) >= 4:
                    self.log_test(
                        "Scene Snapshot - Textboxes Found",
                        True,
                        f"Found {len(textbox_elements)} textbox elements",
                        {"textbox_count": len(textbox_elements), "total_elements": len(elements)}
                    )
                    
                    # Log first 4 textbox element IDs and their cells
                    for i, element in enumerate(textbox_elements[:4]):
                        element_id = element.get("id", f"element_{i}")
                        cell = element.get("cell", element.get("position", "unknown"))
                        print(f"   Textbox {i+1}: ID={element_id}, Cell={cell}")
                    
                    return textbox_elements[:4]  # Return first 4 textboxes
                else:
                    self.log_test(
                        "Scene Snapshot - Insufficient Textboxes",
                        False,
                        f"Found only {len(textbox_elements)} textboxes, need at least 4",
                        {"textbox_count": len(textbox_elements), "total_elements": len(elements)}
                    )
                    return None
            else:
                self.log_test(
                    "Scene Snapshot - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return None
                
        except Exception as e:
            self.log_test(
                "Scene Snapshot - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return None
    
    def fill_registration_form(self, textbox_elements):
        """STEPS 4-7: Fill form fields sequentially"""
        form_data = [
            ("username", "testuser123"),
            ("email", "test@example.com"),
            ("password", "SecurePass123!"),
            ("confirm_password", "SecurePass123!")
        ]
        
        for i, (field_name, field_value) in enumerate(form_data):
            if i >= len(textbox_elements):
                self.log_test(
                    f"Fill {field_name} - No Element",
                    False,
                    f"No textbox element available for {field_name} (index {i})",
                    {"field_index": i, "available_elements": len(textbox_elements)}
                )
                return False
            
            element = textbox_elements[i]
            cell = element.get("cell", element.get("position"))
            
            print(f"   Filling {field_name} in cell {cell}...")
            
            # Click on textbox first
            if not self.click_element_cell(cell, f"Click {field_name} field"):
                return False
            
            # Type the value
            if not self.type_in_cell(cell, field_value, f"Type {field_name}"):
                return False
            
            # Small delay between fields
            time.sleep(1)
        
        return True
    
    def click_element_cell(self, cell, action_name):
        """Click on a specific cell"""
        payload = {
            "session_id": self.session_id,
            "cell": cell
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/remote-click",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "screenshot_base64" in data:
                    self.log_test(
                        action_name,
                        True,
                        f"Successfully clicked cell {cell}",
                        {"cell": cell, "has_screenshot": True}
                    )
                    return True
                else:
                    self.log_test(
                        action_name,
                        False,
                        f"Click response missing screenshot for cell {cell}",
                        {"cell": cell, "response_keys": list(data.keys())}
                    )
                    return False
            else:
                self.log_test(
                    action_name,
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "cell": cell}
                )
                return False
                
        except Exception as e:
            self.log_test(
                action_name,
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "cell": cell}
            )
            return False
    
    def type_in_cell(self, cell, text, action_name):
        """Type text in a specific cell"""
        payload = {
            "session_id": self.session_id,
            "cell": cell,
            "text": text
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/remote-type",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if "screenshot_base64" in data:
                    self.log_test(
                        action_name,
                        True,
                        f"Successfully typed '{text}' in cell {cell}",
                        {"cell": cell, "text": text, "has_screenshot": True}
                    )
                    return True
                else:
                    self.log_test(
                        action_name,
                        False,
                        f"Type response missing screenshot for cell {cell}",
                        {"cell": cell, "text": text, "response_keys": list(data.keys())}
                    )
                    return False
            else:
                self.log_test(
                    action_name,
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "cell": cell}
                )
                return False
                
        except Exception as e:
            self.log_test(
                action_name,
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "cell": cell}
            )
            return False
    
    def click_register_button(self):
        """STEP 8: Find and click REGISTER button"""
        # First get scene to find the REGISTER button
        payload = {
            "session_id": self.session_id
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/scene/snapshot",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                elements = data.get("scene", {}).get("elements", [])
                if not elements:
                    elements = data.get("elements", [])
                
                # Find REGISTER button
                register_button = None
                for element in elements:
                    text = element.get("text", "").upper()
                    label = element.get("label", "").upper()
                    element_type = element.get("type", "").lower()
                    tag_name = element.get("tag_name", "").lower()
                    
                    if ("REGISTER" in text or "REGISTER" in label or 
                        (element_type == "button" and "REGISTER" in str(element).upper()) or
                        (tag_name == "button" and "REGISTER" in str(element).upper())):
                        register_button = element
                        break
                
                if register_button:
                    button_cell = register_button.get("cell", register_button.get("position"))
                    
                    self.log_test(
                        "Find Register Button - Success",
                        True,
                        f"Found REGISTER button at cell {button_cell}",
                        {"button_cell": button_cell, "button_element": register_button}
                    )
                    
                    # Click the REGISTER button
                    return self.click_element_cell(button_cell, "Click REGISTER Button")
                else:
                    self.log_test(
                        "Find Register Button - Not Found",
                        False,
                        "REGISTER button not found in scene elements",
                        {"total_elements": len(elements)}
                    )
                    return False
            else:
                self.log_test(
                    "Find Register Button - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Find Register Button - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return False
    
    def verify_registration_result(self):
        """STEP 9: Verify registration result"""
        # Get final scene/snapshot
        payload = {
            "session_id": self.session_id
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/scene/snapshot",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check current URL
                current_url = data.get("url", "")
                
                # Check if URL changed from /register
                url_changed = current_url and "/register" not in current_url
                
                # Look for success/error messages in elements
                elements = data.get("scene", {}).get("elements", [])
                if not elements:
                    elements = data.get("elements", [])
                
                success_indicators = []
                error_indicators = []
                
                for element in elements:
                    text = element.get("text", "").lower()
                    label = element.get("label", "").lower()
                    
                    # Look for success indicators
                    if any(word in text or word in label for word in 
                           ["success", "welcome", "registered", "complete", "dashboard", "profile"]):
                        success_indicators.append(element)
                    
                    # Look for error indicators
                    if any(word in text or word in label for word in 
                           ["error", "failed", "invalid", "required", "missing"]):
                        error_indicators.append(element)
                
                # Determine result
                if url_changed and success_indicators:
                    self.log_test(
                        "Registration Verification - Success",
                        True,
                        f"Registration appears successful - URL changed to {current_url}, found {len(success_indicators)} success indicators",
                        {
                            "url_changed": url_changed,
                            "current_url": current_url,
                            "success_indicators": len(success_indicators),
                            "error_indicators": len(error_indicators)
                        }
                    )
                    return True
                elif error_indicators:
                    self.log_test(
                        "Registration Verification - Error Detected",
                        False,
                        f"Registration failed - found {len(error_indicators)} error indicators",
                        {
                            "url_changed": url_changed,
                            "current_url": current_url,
                            "success_indicators": len(success_indicators),
                            "error_indicators": len(error_indicators)
                        }
                    )
                    return False
                elif url_changed:
                    self.log_test(
                        "Registration Verification - URL Changed",
                        True,
                        f"Registration may be successful - URL changed to {current_url} (no clear success/error messages)",
                        {
                            "url_changed": url_changed,
                            "current_url": current_url,
                            "success_indicators": len(success_indicators),
                            "error_indicators": len(error_indicators)
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Registration Verification - Inconclusive",
                        False,
                        f"Registration result unclear - URL still contains register: {current_url}",
                        {
                            "url_changed": url_changed,
                            "current_url": current_url,
                            "success_indicators": len(success_indicators),
                            "error_indicators": len(error_indicators)
                        }
                    )
                    return False
            else:
                self.log_test(
                    "Registration Verification - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Registration Verification - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return False
    
    def print_summary(self):
        """Print test summary"""
        print("\n" + "=" * 80)
        print("🎯 JUSTFANS.UNO REGISTRATION AUTOMATION TEST SUMMARY")
        print("=" * 80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["success"])
        failed_tests = total_tests - passed_tests
        
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "📈 Success Rate: 0%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"   • {result['test']}: {result['message']}")
        
        print("\n" + "=" * 80)
        
        return passed_tests == total_tests

def main():
    """Run JustFans.uno registration automation test"""
    print("🚀 Starting JustFans.uno Registration Automation Test")
    print("=" * 80)
    
    tester = JustFansRegistrationTester()
    
    # Run the complete registration flow test
    success = tester.test_justfans_registration_flow()
    
    # Print summary
    overall_success = tester.print_summary()
    
    if overall_success:
        print("🎉 ALL TESTS PASSED - JustFans.uno automation flow working correctly!")
    else:
        print("⚠️  SOME TESTS FAILED - Check the details above for issues")
    
    return overall_success

if __name__ == "__main__":
    main()