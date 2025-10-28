#!/usr/bin/env python3
"""
Automation Smoke Tests for Browser Automation System
Tests specific automation endpoints as requested in review
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://ai-browser-auto.preview.emergentagent.com/api"

class AutomationSmokeTest:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
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
    
    def test_grid_set_endpoint(self):
        """Test 1: POST /api/automation/grid/set with {rows:48, cols:64}"""
        print("\n🧪 Testing Grid Set Endpoint...")
        
        payload = {
            "rows": 48,
            "cols": 64
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/grid/set",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for success and echoed values
                if (data.get('success') == True and 
                    data.get('rows') == 48 and 
                    data.get('cols') == 64):
                    self.log_test(
                        "Grid Set - Success",
                        True,
                        f"Grid set successfully: {data.get('rows')}x{data.get('cols')}",
                        {"payload": payload, "response": data}
                    )
                    return True
                else:
                    self.log_test(
                        "Grid Set - Invalid Response",
                        False,
                        "Response missing success=true or incorrect rows/cols",
                        {"expected": payload, "actual": data}
                    )
                    return False
            else:
                self.log_test(
                    "Grid Set - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "payload": payload}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Grid Set - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "payload": payload}
            )
            return False
    
    def test_smoke_check_endpoint(self):
        """Test 2: POST /api/automation/smoke-check with google.com"""
        print("\n🧪 Testing Smoke Check Endpoint...")
        
        payload = {
            "url": "https://google.com",
            "use_proxy": False
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/smoke-check",
                json=payload,
                timeout=45  # Longer timeout for browser automation
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check all required fields
                required_checks = {
                    'success': True,
                    'session_id': lambda x: x is not None and len(str(x)) > 0,
                    'screenshot_base64': lambda x: x is not None and len(str(x)) > 0,
                    'grid': lambda x: x is not None,
                    'viewport': lambda x: x is not None,
                    'vision': lambda x: isinstance(x, list) and len(x) >= 3
                }
                
                all_passed = True
                failed_checks = []
                
                for field, expected in required_checks.items():
                    value = data.get(field)
                    if callable(expected):
                        if not expected(value):
                            all_passed = False
                            failed_checks.append(f"{field}: {value}")
                    else:
                        if value != expected:
                            all_passed = False
                            failed_checks.append(f"{field}: expected {expected}, got {value}")
                
                if all_passed:
                    self.session_id = data.get('session_id')
                    self.log_test(
                        "Smoke Check - Success",
                        True,
                        f"Smoke check passed with session_id: {self.session_id}",
                        {
                            "session_id": self.session_id,
                            "screenshot_length": len(str(data.get('screenshot_base64', ''))),
                            "vision_count": len(data.get('vision', [])),
                            "has_viewport": bool(data.get('viewport')),
                            "has_grid": bool(data.get('grid'))
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Smoke Check - Failed Validation",
                        False,
                        f"Failed validation checks: {failed_checks}",
                        {"failed_checks": failed_checks, "response_keys": list(data.keys())}
                    )
                    return False
            else:
                self.log_test(
                    "Smoke Check - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "payload": payload}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Smoke Check - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "payload": payload}
            )
            return False
    
    def test_click_cell_endpoint(self):
        """Test 3: POST /api/automation/click-cell with mid-screen cell"""
        print("\n🧪 Testing Click Cell Endpoint...")
        
        if not self.session_id:
            self.log_test(
                "Click Cell - No Session ID",
                False,
                "No session_id available from smoke-check test",
                {"session_id": self.session_id}
            )
            return False
        
        # Use mid-screen cell as requested
        payload = {
            "session_id": self.session_id,
            "cell": "M12"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/click-cell",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for screenshot_base64 and dom_event.cell
                if ('screenshot_base64' in data and 
                    data.get('screenshot_base64') and
                    'dom_event' in data and
                    data.get('dom_event', {}).get('cell') == "M12"):
                    
                    self.log_test(
                        "Click Cell - Success",
                        True,
                        f"Cell click successful: {data.get('dom_event', {}).get('cell')}",
                        {
                            "cell": data.get('dom_event', {}).get('cell'),
                            "screenshot_length": len(str(data.get('screenshot_base64', ''))),
                            "session_id": self.session_id
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Click Cell - Missing Fields",
                        False,
                        "Response missing screenshot_base64 or dom_event.cell",
                        {
                            "has_screenshot": bool(data.get('screenshot_base64')),
                            "dom_event": data.get('dom_event'),
                            "response_keys": list(data.keys())
                        }
                    )
                    return False
            else:
                self.log_test(
                    "Click Cell - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "payload": payload}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Click Cell - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "payload": payload}
            )
            return False
    
    def test_hook_log_endpoint(self):
        """Test 4: GET /api/hook/log - verify observation object"""
        print("\n🧪 Testing Hook Log Endpoint...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/hook/log",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check for observation object
                if 'observation' in data and data.get('observation') is not None:
                    observation = data.get('observation')
                    
                    # Check if vision is echoed (if possible)
                    has_vision = 'vision' in observation if isinstance(observation, dict) else False
                    
                    self.log_test(
                        "Hook Log - Success",
                        True,
                        f"Hook log retrieved with observation object",
                        {
                            "has_observation": True,
                            "observation_type": type(observation).__name__,
                            "has_vision": has_vision,
                            "observation_keys": list(observation.keys()) if isinstance(observation, dict) else None
                        }
                    )
                    return True
                else:
                    self.log_test(
                        "Hook Log - Missing Observation",
                        False,
                        "Response missing observation object",
                        {"response_keys": list(data.keys()), "observation": data.get('observation')}
                    )
                    return False
            else:
                self.log_test(
                    "Hook Log - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                return False
                
        except Exception as e:
            self.log_test(
                "Hook Log - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
            return False
    
    def test_hook_control_endpoint(self):
        """Test 5: POST /api/hook/control - PAUSED and STOP modes"""
        print("\n🧪 Testing Hook Control Endpoint...")
        
        # Test PAUSED mode
        print("   Testing PAUSED mode...")
        payload_pause = {"mode": "PAUSED"}
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/hook/control",
                json=payload_pause,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if agent_status is updated accordingly
                if 'agent_status' in data:
                    agent_status = data.get('agent_status')
                    if 'PAUSED' in str(agent_status).upper() or 'PAUSE' in str(agent_status).upper():
                        self.log_test(
                            "Hook Control - PAUSED Mode",
                            True,
                            f"Agent status updated to paused: {agent_status}",
                            {"mode": "PAUSED", "agent_status": agent_status}
                        )
                        paused_success = True
                    else:
                        self.log_test(
                            "Hook Control - PAUSED Mode Failed",
                            False,
                            f"Agent status not updated to paused: {agent_status}",
                            {"mode": "PAUSED", "agent_status": agent_status}
                        )
                        paused_success = False
                else:
                    self.log_test(
                        "Hook Control - PAUSED Mode Missing Status",
                        False,
                        "Response missing agent_status field",
                        {"mode": "PAUSED", "response_keys": list(data.keys())}
                    )
                    paused_success = False
            else:
                self.log_test(
                    "Hook Control - PAUSED Mode HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "mode": "PAUSED"}
                )
                paused_success = False
                
        except Exception as e:
            self.log_test(
                "Hook Control - PAUSED Mode Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "mode": "PAUSED"}
            )
            paused_success = False
        
        # Test STOP mode
        print("   Testing STOP mode...")
        payload_stop = {"mode": "STOP"}
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/hook/control",
                json=payload_stop,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if agent_status returns to IDLE
                if 'agent_status' in data:
                    agent_status = data.get('agent_status')
                    if 'IDLE' in str(agent_status).upper():
                        self.log_test(
                            "Hook Control - STOP Mode",
                            True,
                            f"Agent status returned to idle: {agent_status}",
                            {"mode": "STOP", "agent_status": agent_status}
                        )
                        stop_success = True
                    else:
                        self.log_test(
                            "Hook Control - STOP Mode Failed",
                            False,
                            f"Agent status not returned to idle: {agent_status}",
                            {"mode": "STOP", "agent_status": agent_status}
                        )
                        stop_success = False
                else:
                    self.log_test(
                        "Hook Control - STOP Mode Missing Status",
                        False,
                        "Response missing agent_status field",
                        {"mode": "STOP", "response_keys": list(data.keys())}
                    )
                    stop_success = False
            else:
                self.log_test(
                    "Hook Control - STOP Mode HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code, "mode": "STOP"}
                )
                stop_success = False
                
        except Exception as e:
            self.log_test(
                "Hook Control - STOP Mode Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__, "mode": "STOP"}
            )
            stop_success = False
        
        return paused_success and stop_success
    
    def run_all_tests(self):
        """Run all automation smoke tests in sequence"""
        print("🚀 Starting Automation Smoke Tests...")
        print("=" * 60)
        
        # Test sequence as requested
        test_results = []
        
        # Test 1: Grid Set
        test_results.append(self.test_grid_set_endpoint())
        
        # Test 2: Smoke Check (depends on grid set)
        test_results.append(self.test_smoke_check_endpoint())
        
        # Test 3: Click Cell (depends on smoke check session)
        test_results.append(self.test_click_cell_endpoint())
        
        # Test 4: Hook Log
        test_results.append(self.test_hook_log_endpoint())
        
        # Test 5: Hook Control
        test_results.append(self.test_hook_control_endpoint())
        
        # Summary
        passed_tests = sum(test_results)
        total_tests = len(test_results)
        
        print("\n" + "=" * 60)
        print(f"🏁 AUTOMATION SMOKE TESTS COMPLETE")
        print(f"📊 Results: {passed_tests}/{total_tests} tests passed ({passed_tests/total_tests*100:.1f}%)")
        
        if passed_tests == total_tests:
            print("✅ ALL TESTS PASSED - Automation system is working correctly")
        else:
            print("❌ SOME TESTS FAILED - Check individual test results above")
        
        # Print detailed results
        print("\n📋 Detailed Test Results:")
        for result in self.test_results:
            status = "✅" if result['success'] else "❌"
            print(f"   {status} {result['test']}: {result['message']}")
        
        return passed_tests, total_tests, self.test_results

def main():
    """Main test execution"""
    tester = AutomationSmokeTest()
    passed, total, results = tester.run_all_tests()
    
    # Return results for potential integration
    return {
        "passed": passed,
        "total": total,
        "success_rate": passed/total if total > 0 else 0,
        "results": results
    }

if __name__ == "__main__":
    main()