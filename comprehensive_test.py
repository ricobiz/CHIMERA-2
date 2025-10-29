#!/usr/bin/env python3
"""
Comprehensive Backend Testing - Review Request Systems
Tests the specific systems mentioned in the review request
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://aios-automation.preview.emergentagent.com/api"

class ComprehensiveTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
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
    
    def test_self_improvement_health_check(self):
        """Test GET /api/self-improvement/health-check endpoint"""
        print("\n🧪 Testing Self-Improvement Health Check...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/self-improvement/health-check",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['timestamp', 'services', 'code_metrics']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    services = data.get('services', {})
                    expected_services = ['backend', 'frontend', 'mongodb', 'nginx-code-proxy', 'code-server']
                    
                    # Check if services are present
                    found_services = list(services.keys())
                    running_services = [s for s, info in services.items() if info.get('status') == 'RUNNING']
                    
                    self.log_test(
                        "Self-Improvement Health Check",
                        True,
                        f"Health check completed. Found {len(found_services)} services, {len(running_services)} running",
                        {
                            "services_found": found_services,
                            "running_services": running_services,
                            "code_metrics": data.get('code_metrics', {})
                        }
                    )
                else:
                    self.log_test(
                        "Self-Improvement Health Check - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Self-Improvement Health Check - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Self-Improvement Health Check - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_self_improvement_analyze_code(self):
        """Test POST /api/self-improvement/analyze-code endpoint"""
        print("\n🧪 Testing Self-Improvement Code Analysis...")
        
        payload = {
            "target": "backend",
            "focus_areas": ["performance", "security"]
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/self-improvement/analyze-code",
                json=payload,
                timeout=60  # Longer timeout for AI analysis
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['overall_health_score', 'critical_issues', 'improvements', 'summary']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    health_score = data.get('overall_health_score', 0)
                    critical_issues = data.get('critical_issues', [])
                    improvements = data.get('improvements', [])
                    
                    if isinstance(health_score, (int, float)) and 0 <= health_score <= 100:
                        self.log_test(
                            "Self-Improvement Code Analysis",
                            True,
                            f"Code analysis completed. Health score: {health_score}/100, {len(critical_issues)} critical issues, {len(improvements)} improvements",
                            {
                                "health_score": health_score,
                                "critical_issues_count": len(critical_issues),
                                "improvements_count": len(improvements),
                                "focus_areas": payload["focus_areas"]
                            }
                        )
                    else:
                        self.log_test(
                            "Self-Improvement Code Analysis - Invalid Score",
                            False,
                            f"Invalid health score: {health_score}",
                            {"health_score": health_score}
                        )
                else:
                    self.log_test(
                        "Self-Improvement Code Analysis - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Self-Improvement Code Analysis - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Self-Improvement Code Analysis - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_self_improvement_project_structure(self):
        """Test GET /api/self-improvement/project-structure endpoint"""
        print("\n🧪 Testing Self-Improvement Project Structure...")
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/self-improvement/project-structure",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['structure', 'total_files', 'total_lines']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    structure = data.get('structure', {})
                    total_files = data.get('total_files', 0)
                    total_lines = data.get('total_lines', 0)
                    
                    # Check if backend and frontend are in structure
                    has_backend = 'backend' in structure
                    has_frontend = 'frontend' in structure
                    
                    if has_backend and has_frontend and total_files > 0:
                        self.log_test(
                            "Self-Improvement Project Structure",
                            True,
                            f"Project structure retrieved. {total_files} files, {total_lines} lines of code",
                            {
                                "total_files": total_files,
                                "total_lines": total_lines,
                                "has_backend": has_backend,
                                "has_frontend": has_frontend
                            }
                        )
                    else:
                        self.log_test(
                            "Self-Improvement Project Structure - Invalid Structure",
                            False,
                            "Project structure missing backend/frontend or no files found",
                            {
                                "has_backend": has_backend,
                                "has_frontend": has_frontend,
                                "total_files": total_files
                            }
                        )
                else:
                    self.log_test(
                        "Self-Improvement Project Structure - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Self-Improvement Project Structure - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Self-Improvement Project Structure - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_document_verification_analyze(self):
        """Test POST /api/document-verification/analyze endpoint"""
        print("\n🧪 Testing Document Verification Analysis...")
        
        # Create a small test image (1x1 pixel PNG in base64)
        test_image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        
        payload = {
            "document_base64": test_image_base64,
            "document_type": "general"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/document-verification/analyze",
                json=payload,
                timeout=90  # Longer timeout for AI analysis
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['verdict', 'fraud_probability', 'multi_model_analysis']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    verdict = data.get('verdict')
                    fraud_probability = data.get('fraud_probability', 0)
                    multi_model = data.get('multi_model_analysis', {})
                    
                    # Check if verdict is valid
                    valid_verdicts = ['AUTHENTIC', 'SUSPICIOUS', 'LIKELY_FAKE']
                    if verdict in valid_verdicts and isinstance(fraud_probability, (int, float)):
                        # Check if multi-model analysis has GPT-5 and Claude
                        has_gpt5 = 'primary_model' in multi_model and 'GPT-5' in str(multi_model.get('primary_model', {}))
                        has_claude = 'secondary_model' in multi_model and 'Claude' in str(multi_model.get('secondary_model', {}))
                        
                        self.log_test(
                            "Document Verification Analysis",
                            True,
                            f"Document analysis completed. Verdict: {verdict}, Fraud probability: {fraud_probability}%",
                            {
                                "verdict": verdict,
                                "fraud_probability": fraud_probability,
                                "has_gpt5_analysis": has_gpt5,
                                "has_claude_analysis": has_claude,
                                "multi_model_agreement": multi_model.get('agreement_level', 'N/A')
                            }
                        )
                    else:
                        self.log_test(
                            "Document Verification Analysis - Invalid Response",
                            False,
                            f"Invalid verdict ({verdict}) or fraud probability ({fraud_probability})",
                            {"verdict": verdict, "fraud_probability": fraud_probability}
                        )
                else:
                    self.log_test(
                        "Document Verification Analysis - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Document Verification Analysis - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Document Verification Analysis - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_planning_generate(self):
        """Test POST /api/planning/generate endpoint"""
        print("\n🧪 Testing Planning System - Generate Plan...")
        
        payload = {
            "goal": "Navigate to google.com and search for 'test'"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/planning/generate",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['plan', 'complexity', 'estimatedSteps']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    plan = data.get('plan', {})
                    steps = plan.get('steps', [])
                    complexity = data.get('complexity')
                    
                    # Check if plan has steps with required action types
                    action_types = [step.get('actionType') for step in steps]
                    expected_actions = ['NAVIGATE', 'TYPE', 'CLICK']
                    has_expected_actions = any(action in action_types for action in expected_actions)
                    
                    if len(steps) > 0 and has_expected_actions and complexity:
                        self.log_test(
                            "Planning Generate",
                            True,
                            f"Plan generated successfully. {len(steps)} steps, complexity: {complexity}",
                            {
                                "steps_count": len(steps),
                                "complexity": complexity,
                                "action_types": action_types,
                                "goal": payload["goal"]
                            }
                        )
                    else:
                        self.log_test(
                            "Planning Generate - Invalid Plan",
                            False,
                            f"Plan missing steps or expected actions. Steps: {len(steps)}, Actions: {action_types}",
                            {"steps_count": len(steps), "action_types": action_types}
                        )
                else:
                    self.log_test(
                        "Planning Generate - Missing Fields",
                        False,
                        f"Response missing fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Planning Generate - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Planning Generate - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_browser_automation_comprehensive(self):
        """Comprehensive test of browser automation system as requested"""
        print("\n🧪 Testing Browser Automation - Comprehensive Flow...")
        
        # Test 1: Create Session
        session_id = "test-session-123"
        
        try:
            # Create session
            create_response = self.session.post(
                f"{BACKEND_URL}/automation/session/create",
                json={"session_id": session_id},
                timeout=30
            )
            
            if create_response.status_code == 200:
                create_data = create_response.json()
                if create_data.get('session_id') == session_id:
                    self.log_test(
                        "Browser Automation - Create Session",
                        True,
                        f"Session created successfully: {session_id}",
                        {"session_id": session_id, "status": create_data.get('status')}
                    )
                    
                    # Test 2: Navigate to Google
                    try:
                        navigate_response = self.session.post(
                            f"{BACKEND_URL}/automation/navigate",
                            json={"session_id": session_id, "url": "https://google.com"},
                            timeout=45
                        )
                        
                        if navigate_response.status_code == 200:
                            navigate_data = navigate_response.json()
                            if 'screenshot' in navigate_data:
                                self.log_test(
                                    "Browser Automation - Navigate to Google",
                                    True,
                                    "Successfully navigated to Google with screenshot",
                                    {"url": "https://google.com", "has_screenshot": True}
                                )
                                
                                # Test 3: Get Screenshot
                                try:
                                    screenshot_response = self.session.get(
                                        f"{BACKEND_URL}/automation/screenshot/{session_id}",
                                        timeout=30
                                    )
                                    
                                    if screenshot_response.status_code == 200:
                                        screenshot_data = screenshot_response.json()
                                        if 'screenshot' in screenshot_data:
                                            screenshot_b64 = screenshot_data['screenshot']
                                            self.log_test(
                                                "Browser Automation - Get Screenshot",
                                                True,
                                                f"Screenshot captured successfully ({len(screenshot_b64)} chars)",
                                                {"screenshot_length": len(screenshot_b64)}
                                            )
                                        else:
                                            self.log_test(
                                                "Browser Automation - Get Screenshot - No Data",
                                                False,
                                                "Screenshot response missing screenshot field",
                                                {"response_keys": list(screenshot_data.keys())}
                                            )
                                    else:
                                        self.log_test(
                                            "Browser Automation - Get Screenshot - HTTP Error",
                                            False,
                                            f"HTTP {screenshot_response.status_code}: {screenshot_response.text}",
                                            {"status_code": screenshot_response.status_code}
                                        )
                                        
                                except Exception as e:
                                    self.log_test(
                                        "Browser Automation - Get Screenshot - Exception",
                                        False,
                                        f"Screenshot error: {str(e)}",
                                        {"error_type": type(e).__name__}
                                    )
                            else:
                                self.log_test(
                                    "Browser Automation - Navigate - No Screenshot",
                                    False,
                                    "Navigation response missing screenshot",
                                    {"response_keys": list(navigate_data.keys())}
                                )
                        else:
                            self.log_test(
                                "Browser Automation - Navigate - HTTP Error",
                                False,
                                f"HTTP {navigate_response.status_code}: {navigate_response.text}",
                                {"status_code": navigate_response.status_code}
                            )
                            
                    except Exception as e:
                        self.log_test(
                            "Browser Automation - Navigate - Exception",
                            False,
                            f"Navigation error: {str(e)}",
                            {"error_type": type(e).__name__}
                        )
                else:
                    self.log_test(
                        "Browser Automation - Create Session - Invalid Response",
                        False,
                        "Session creation response invalid",
                        {"expected_session": session_id, "actual_session": create_data.get('session_id')}
                    )
            else:
                self.log_test(
                    "Browser Automation - Create Session - HTTP Error",
                    False,
                    f"HTTP {create_response.status_code}: {create_response.text}",
                    {"status_code": create_response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Browser Automation - Create Session - Exception",
                False,
                f"Session creation error: {str(e)}",
                {"error_type": type(e).__name__}
            )

    def run_comprehensive_tests(self):
        """Run comprehensive tests for all systems mentioned in review request"""
        print("🔍 COMPREHENSIVE TESTING - Все системы приложения")
        print(f"Backend URL: {BACKEND_URL}")
        print("=" * 80)
        
        # 1. SELF-IMPROVEMENT SYSTEM
        print("\n🧠 1. SELF-IMPROVEMENT SYSTEM")
        print("-" * 40)
        self.test_self_improvement_health_check()
        self.test_self_improvement_analyze_code()
        self.test_self_improvement_project_structure()
        
        # 2. DOCUMENT VERIFICATION SYSTEM
        print("\n📄 2. DOCUMENT VERIFICATION SYSTEM")
        print("-" * 40)
        self.test_document_verification_analyze()
        
        # 3. PLANNING SYSTEM
        print("\n📋 3. PLANNING SYSTEM")
        print("-" * 40)
        self.test_planning_generate()
        
        # 4. BROWSER AUTOMATION SYSTEM
        print("\n🤖 4. BROWSER AUTOMATION SYSTEM")
        print("-" * 40)
        self.test_browser_automation_comprehensive()
        
        # Summary
        print("\n" + "=" * 80)
        print("📊 COMPREHENSIVE TEST SUMMARY")
        print("=" * 80)
        
        passed = sum(1 for result in self.test_results if result['success'])
        failed = len(self.test_results) - passed
        
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {(passed/len(self.test_results)*100):.1f}%")
        
        if failed > 0:
            print("\n🔍 FAILED TESTS:")
            for result in self.test_results:
                if not result['success']:
                    print(f"   ❌ {result['test']}: {result['message']}")
        
        return passed, failed

if __name__ == "__main__":
    tester = ComprehensiveTester()
    tester.run_comprehensive_tests()