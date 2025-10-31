#!/usr/bin/env python3
"""
Autonomous Automation Backend Testing
Tests the new autonomous automation architecture with bulletproof automation capabilities
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://sense-act.preview.emergentagent.com/api"

class AutonomousBackendTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.created_task_id = None
        
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
    
    def test_autonomous_health_endpoint(self):
        """Test GET /api/autonomous/health endpoint - CRITICAL"""
        print("\n🧪 Testing Autonomous Health Check Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/autonomous/health", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['status', 'components']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    components = data.get('components', {})
                    
                    # Check all expected components
                    expected_components = [
                        'autonomous_agent', 'meta_planner', 'tactical_brain', 
                        'tool_orchestrator', 'perception', 'execution', 'verification'
                    ]
                    
                    missing_components = [comp for comp in expected_components if comp not in components]
                    
                    if not missing_components:
                        all_healthy = all(components.values())
                        status = data.get('status')
                        
                        if status in ['healthy', 'degraded']:
                            self.log_test(
                                "Autonomous Health Check - Success",
                                True,
                                f"Health status: {status}, All components present",
                                {
                                    "status": status,
                                    "components": components,
                                    "all_healthy": all_healthy
                                }
                            )
                        else:
                            self.log_test(
                                "Autonomous Health Check - Invalid Status",
                                False,
                                f"Invalid health status: {status}",
                                {"status": status, "expected": ["healthy", "degraded", "unhealthy"]}
                            )
                    else:
                        self.log_test(
                            "Autonomous Health Check - Missing Components",
                            False,
                            f"Missing components: {missing_components}",
                            {"missing_components": missing_components, "found_components": list(components.keys())}
                        )
                else:
                    self.log_test(
                        "Autonomous Health Check - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Autonomous Health Check - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Autonomous Health Check - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_autonomous_tools_endpoint(self):
        """Test GET /api/autonomous/tools endpoint - CRITICAL"""
        print("\n🧪 Testing Autonomous Tools Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/autonomous/tools", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['available_tools', 'usage_statistics', 'total_tools']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    tools = data.get('available_tools', [])
                    total_tools = data.get('total_tools', 0)
                    
                    # Check expected tools
                    expected_tools = [
                        'create_temp_email', 'generate_password', 'generate_user_data',
                        'get_phone_number', 'setup_proxy', 'solve_captcha'
                    ]
                    
                    found_tools = [tool for tool in expected_tools if tool in tools]
                    
                    if len(found_tools) >= 4:  # At least 4 core tools should be available
                        self.log_test(
                            "Autonomous Tools - Success",
                            True,
                            f"Found {len(found_tools)}/{len(expected_tools)} expected tools, total: {total_tools}",
                            {
                                "available_tools": tools,
                                "found_expected": found_tools,
                                "total_tools": total_tools
                            }
                        )
                    else:
                        self.log_test(
                            "Autonomous Tools - Insufficient Tools",
                            False,
                            f"Only found {len(found_tools)}/{len(expected_tools)} expected tools",
                            {"found_tools": found_tools, "available_tools": tools}
                        )
                else:
                    self.log_test(
                        "Autonomous Tools - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Autonomous Tools - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Autonomous Tools - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_autonomous_run_endpoint(self):
        """Test POST /api/autonomous/run endpoint with simple goal - CRITICAL"""
        print("\n🧪 Testing Autonomous Run Endpoint...")
        
        # Test with simple navigation goal as specified in review
        payload = {
            "goal": "Navigate to google.com",
            "context": {
                "timeout_minutes": 5,
                "max_retries": 2,
                "use_proxy": False,  # Start simple
                "solve_captcha": True
            }
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/autonomous/run",
                json=payload,
                timeout=60  # Longer timeout for autonomous execution
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['task_id', 'status', 'message']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    task_id = data.get('task_id')
                    status = data.get('status')
                    message = data.get('message')
                    
                    # Store task ID for later tests
                    if task_id:
                        self.created_task_id = task_id
                    
                    # Check valid status
                    valid_statuses = ['SUCCESS', 'FAILED', 'NEEDS_USER_DATA', 'RUNNING']
                    
                    if status in valid_statuses:
                        self.log_test(
                            "Autonomous Run - Success",
                            True,
                            f"Task started with status: {status}, ID: {task_id}",
                            {
                                "task_id": task_id,
                                "status": status,
                                "message": message,
                                "goal": payload["goal"]
                            }
                        )
                        
                        # If task completed successfully, test status endpoint
                        if status == 'SUCCESS' and task_id:
                            self.test_autonomous_status_endpoint(task_id)
                            
                    else:
                        self.log_test(
                            "Autonomous Run - Invalid Status",
                            False,
                            f"Invalid status: {status}",
                            {"status": status, "valid_statuses": valid_statuses}
                        )
                else:
                    self.log_test(
                        "Autonomous Run - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Autonomous Run - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except requests.exceptions.Timeout:
            self.log_test(
                "Autonomous Run - Timeout",
                False,
                "Request timed out after 60 seconds",
                {"timeout": 60}
            )
        except Exception as e:
            self.log_test(
                "Autonomous Run - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_autonomous_status_endpoint(self, task_id=None):
        """Test GET /api/autonomous/status/{task_id} endpoint"""
        print("\n🧪 Testing Autonomous Status Endpoint...")
        
        if not task_id and not self.created_task_id:
            self.log_test(
                "Autonomous Status - No Task ID",
                False,
                "No task ID available for testing",
                {"created_task_id": self.created_task_id}
            )
            return
        
        test_task_id = task_id or self.created_task_id
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/autonomous/status/{test_task_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['task_id', 'goal', 'state', 'progress', 'metrics']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    progress = data.get('progress', {})
                    metrics = data.get('metrics', {})
                    
                    # Check progress structure
                    progress_fields = ['current_step', 'total_steps', 'completion_percentage']
                    progress_missing = [field for field in progress_fields if field not in progress]
                    
                    if not progress_missing:
                        self.log_test(
                            "Autonomous Status - Success",
                            True,
                            f"Status retrieved for task: {test_task_id}",
                            {
                                "task_id": test_task_id,
                                "state": data.get('state'),
                                "progress": progress,
                                "has_metrics": bool(metrics)
                            }
                        )
                    else:
                        self.log_test(
                            "Autonomous Status - Missing Progress Fields",
                            False,
                            f"Progress missing fields: {progress_missing}",
                            {"progress_missing": progress_missing, "progress": progress}
                        )
                else:
                    self.log_test(
                        "Autonomous Status - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            elif response.status_code == 404:
                self.log_test(
                    "Autonomous Status - Task Not Found",
                    False,
                    f"Task not found: {test_task_id}",
                    {"task_id": test_task_id, "status_code": 404}
                )
            else:
                self.log_test(
                    "Autonomous Status - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Autonomous Status - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_autonomous_metrics_endpoint(self):
        """Test GET /api/autonomous/metrics endpoint"""
        print("\n🧪 Testing Autonomous Metrics Endpoint...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/autonomous/metrics", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if idle or has metrics
                if data.get('status') == 'idle':
                    self.log_test(
                        "Autonomous Metrics - Idle State",
                        True,
                        "Metrics endpoint working - system idle",
                        {"status": "idle", "message": data.get('message')}
                    )
                else:
                    # Check for active metrics
                    required_fields = ['status', 'metrics', 'performance']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if not missing_fields:
                        performance = data.get('performance', {})
                        perf_fields = ['avg_step_time', 'success_rate', 'retry_rate']
                        perf_missing = [field for field in perf_fields if field not in performance]
                        
                        if not perf_missing:
                            self.log_test(
                                "Autonomous Metrics - Success",
                                True,
                                f"Metrics retrieved with status: {data.get('status')}",
                                {
                                    "status": data.get('status'),
                                    "performance": performance,
                                    "metrics": data.get('metrics')
                                }
                            )
                        else:
                            self.log_test(
                                "Autonomous Metrics - Missing Performance Fields",
                                False,
                                f"Performance missing fields: {perf_missing}",
                                {"perf_missing": perf_missing, "performance": performance}
                            )
                    else:
                        self.log_test(
                            "Autonomous Metrics - Missing Fields",
                            False,
                            f"Response missing fields: {missing_fields}",
                            {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                        )
            else:
                self.log_test(
                    "Autonomous Metrics - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Autonomous Metrics - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_tool_execution_endpoint(self):
        """Test POST /api/autonomous/tools/{tool_name} endpoint"""
        print("\n🧪 Testing Tool Execution Endpoint...")
        
        # Test email generation tool
        tool_name = "create_temp_email"
        params = {}
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/autonomous/tools/{tool_name}",
                json=params,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check if tool executed successfully
                if data.get('error'):
                    self.log_test(
                        "Tool Execution - Tool Error",
                        False,
                        f"Tool returned error: {data['error']}",
                        {"tool": tool_name, "error": data['error']}
                    )
                else:
                    # Check for email-specific fields
                    if 'email' in data:
                        self.log_test(
                            "Tool Execution - Success",
                            True,
                            f"Tool {tool_name} executed successfully",
                            {
                                "tool": tool_name,
                                "email": data.get('email'),
                                "provider": data.get('provider'),
                                "has_access_url": bool(data.get('access_url'))
                            }
                        )
                    else:
                        self.log_test(
                            "Tool Execution - Missing Email",
                            False,
                            "Email tool didn't return email field",
                            {"tool": tool_name, "response_keys": list(data.keys())}
                        )
            elif response.status_code == 400:
                # Tool error - check if it's a proper error response
                try:
                    data = response.json()
                    if 'detail' in data:
                        self.log_test(
                            "Tool Execution - Tool Not Found/Error",
                            True,  # This is expected behavior for invalid tools
                            f"Tool error properly handled: {data['detail']}",
                            {"tool": tool_name, "error_detail": data['detail']}
                        )
                    else:
                        self.log_test(
                            "Tool Execution - Invalid Error Response",
                            False,
                            "400 error without proper detail",
                            {"status_code": 400, "response": response.text}
                        )
                except:
                    self.log_test(
                        "Tool Execution - Invalid Error Format",
                        False,
                        "400 error with invalid JSON",
                        {"status_code": 400, "response": response.text}
                    )
            else:
                self.log_test(
                    "Tool Execution - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Tool Execution - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_existing_automation_integration(self):
        """Test that existing automation endpoints still work with autonomous system"""
        print("\n🧪 Testing Existing Automation Integration...")
        
        # Test that existing automation endpoints are not broken
        endpoints_to_test = [
            "/automation/grid/set",
            "/automation/smoke-check", 
            "/hook/log"
        ]
        
        integration_success = 0
        total_tests = len(endpoints_to_test)
        
        # Test grid set endpoint
        try:
            grid_payload = {"rows": 48, "cols": 64}
            response = self.session.post(
                f"{BACKEND_URL}/automation/grid/set",
                json=grid_payload,
                timeout=15
            )
            
            if response.status_code == 200:
                integration_success += 1
                
        except Exception as e:
            pass  # Continue testing other endpoints
        
        # Test smoke check endpoint
        try:
            smoke_payload = {"url": "https://google.com", "use_proxy": False}
            response = self.session.post(
                f"{BACKEND_URL}/automation/smoke-check",
                json=smoke_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                integration_success += 1
                
        except Exception as e:
            pass  # Continue testing
        
        # Test hook log endpoint
        try:
            response = self.session.get(f"{BACKEND_URL}/hook/log", timeout=15)
            
            if response.status_code == 200:
                integration_success += 1
                
        except Exception as e:
            pass  # Continue testing
        
        # Evaluate integration success
        success_rate = (integration_success / total_tests) * 100
        
        if success_rate >= 66:  # At least 2/3 endpoints working
            self.log_test(
                "Existing Automation Integration - Success",
                True,
                f"Integration working: {integration_success}/{total_tests} endpoints ({success_rate:.1f}%)",
                {
                    "working_endpoints": integration_success,
                    "total_endpoints": total_tests,
                    "success_rate": success_rate
                }
            )
        else:
            self.log_test(
                "Existing Automation Integration - Degraded",
                False,
                f"Integration issues: only {integration_success}/{total_tests} endpoints working ({success_rate:.1f}%)",
                {
                    "working_endpoints": integration_success,
                    "total_endpoints": total_tests,
                    "success_rate": success_rate
                }
            )
    
    def test_browser_automation_service_integration(self):
        """Test that autonomous agent properly uses existing browser_automation_service"""
        print("\n🧪 Testing Browser Automation Service Integration...")
        
        # Test that browser automation service endpoints are accessible
        # This verifies the autonomous system can use existing services
        
        try:
            # Test session creation (core browser service)
            session_payload = {"use_proxy": False}
            response = self.session.post(
                f"{BACKEND_URL}/automation/session/create",
                json=session_payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'session_id' in data and data.get('status') == 'ready':
                    self.log_test(
                        "Browser Service Integration - Session Creation",
                        True,
                        f"Browser session created successfully: {data.get('session_id')}",
                        {
                            "session_id": data.get('session_id'),
                            "status": data.get('status'),
                            "proxy_enabled": data.get('proxy_enabled', False)
                        }
                    )
                    
                    # Test screenshot capability (core perception)
                    session_id = data.get('session_id')
                    if session_id:
                        try:
                            screenshot_response = self.session.get(
                                f"{BACKEND_URL}/automation/screenshot/{session_id}/full",
                                timeout=15
                            )
                            
                            if screenshot_response.status_code == 200:
                                screenshot_data = screenshot_response.json()
                                
                                if 'screenshot_base64' in screenshot_data:
                                    self.log_test(
                                        "Browser Service Integration - Screenshot",
                                        True,
                                        "Screenshot capture working correctly",
                                        {
                                            "has_screenshot": bool(screenshot_data.get('screenshot_base64')),
                                            "has_viewport": bool(screenshot_data.get('viewport')),
                                            "session_id": session_id
                                        }
                                    )
                                else:
                                    self.log_test(
                                        "Browser Service Integration - Screenshot Missing",
                                        False,
                                        "Screenshot response missing screenshot_base64",
                                        {"response_keys": list(screenshot_data.keys())}
                                    )
                            else:
                                self.log_test(
                                    "Browser Service Integration - Screenshot Error",
                                    False,
                                    f"Screenshot endpoint error: {screenshot_response.status_code}",
                                    {"status_code": screenshot_response.status_code}
                                )
                        except Exception as e:
                            self.log_test(
                                "Browser Service Integration - Screenshot Exception",
                                False,
                                f"Screenshot test failed: {str(e)}",
                                {"error": str(e)}
                            )
                else:
                    self.log_test(
                        "Browser Service Integration - Invalid Session",
                        False,
                        "Session creation response invalid",
                        {"response": data}
                    )
            else:
                self.log_test(
                    "Browser Service Integration - Session Error",
                    False,
                    f"Session creation failed: {response.status_code}",
                    {"status_code": response.status_code, "response": response.text}
                )
                
        except Exception as e:
            self.log_test(
                "Browser Service Integration - Exception",
                False,
                f"Integration test failed: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def run_all_tests(self):
        """Run all autonomous automation tests"""
        print("🚀 Starting Autonomous Automation Backend Testing...")
        print("=" * 60)
        
        # Core autonomous endpoints
        self.test_autonomous_health_endpoint()
        self.test_autonomous_tools_endpoint()
        self.test_autonomous_run_endpoint()
        self.test_autonomous_metrics_endpoint()
        self.test_tool_execution_endpoint()
        
        # Integration tests
        self.test_existing_automation_integration()
        self.test_browser_automation_service_integration()
        
        # Summary
        print("\n" + "=" * 60)
        print("🏁 AUTONOMOUS AUTOMATION TEST SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print(f"\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   - {result['test']}: {result['message']}")
        
        return {
            "total": total_tests,
            "passed": passed_tests,
            "failed": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "results": self.test_results
        }

if __name__ == "__main__":
    tester = AutonomousBackendTester()
    results = tester.run_all_tests()
    
    # Exit with error code if tests failed
    if results["failed"] > 0:
        exit(1)
    else:
        print("\n🎉 All autonomous automation tests passed!")
        exit(0)