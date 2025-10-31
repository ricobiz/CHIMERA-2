#!/usr/bin/env python3
"""
Comprehensive Automation Backend Testing - Phase 1
Tests all 15 automation endpoints as specified in the review request
"""

import requests
import json
import time
import uuid
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://agent-control-10.preview.emergentagent.com/api"

class AutomationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        self.session_id = None
        self.screenshot_id = None
        self.scene_data = None
        
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
    
    def test_1_grid_configuration(self):
        """Test 1: POST /api/automation/grid/set - Grid Configuration"""
        print("\n🧪 Test 1: Grid Configuration...")
        
        payload = {
            "rows": 64,
            "cols": 48
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/grid/set",
                json=payload,
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if (data.get('success') == True and 
                    data.get('rows') == 64 and 
                    data.get('cols') == 48):
                    self.log_test(
                        "Grid Configuration",
                        True,
                        f"Grid set to {data['rows']}x{data['cols']} successfully",
                        {"success": data['success'], "rows": data['rows'], "cols": data['cols']}
                    )
                else:
                    self.log_test(
                        "Grid Configuration",
                        False,
                        "Grid configuration response invalid",
                        {"expected": {"success": True, "rows": 64, "cols": 48}, "actual": data}
                    )
            else:
                self.log_test(
                    "Grid Configuration",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Grid Configuration",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_2_session_creation_with_proxy(self):
        """Test 2: POST /api/automation/session/create - Session Creation with Proxy"""
        print("\n🧪 Test 2: Session Creation with Proxy...")
        
        payload = {
            "session_id": "test-session-001",
            "use_proxy": True
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/session/create",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if (data.get('status') == "ready" and 
                    data.get('proxy_enabled') == True and 
                    'session_id' in data):
                    self.session_id = data['session_id']
                    self.log_test(
                        "Session Creation with Proxy",
                        True,
                        f"Session created: {self.session_id}, proxy enabled",
                        {"session_id": self.session_id, "status": data['status'], "proxy_enabled": data['proxy_enabled']}
                    )
                else:
                    self.log_test(
                        "Session Creation with Proxy",
                        False,
                        "Session creation response invalid",
                        {"expected": {"status": "ready", "proxy_enabled": True}, "actual": data}
                    )
            else:
                self.log_test(
                    "Session Creation with Proxy",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Session Creation with Proxy",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_3_smoke_check_google(self):
        """Test 3: POST /api/automation/smoke-check - Smoke Check (Google)"""
        print("\n🧪 Test 3: Smoke Check (Google)...")
        
        payload = {
            "url": "https://google.com",
            "use_proxy": False
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/smoke-check",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['screenshot_base64', 'session_id', 'grid', 'viewport', 'vision']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Validate screenshot_base64 is a base64 string
                    screenshot = data['screenshot_base64']
                    if isinstance(screenshot, str) and len(screenshot) > 100:
                        self.session_id = data['session_id']
                        self.screenshot_id = data.get('screenshot_id')
                        
                        self.log_test(
                            "Smoke Check (Google)",
                            True,
                            f"Google navigation successful, screenshot captured ({len(screenshot)} chars)",
                            {
                                "session_id": self.session_id,
                                "screenshot_id": self.screenshot_id,
                                "screenshot_length": len(screenshot),
                                "grid": data['grid'],
                                "viewport": data['viewport'],
                                "vision_array_length": len(data['vision']) if isinstance(data['vision'], list) else 0
                            }
                        )
                    else:
                        self.log_test(
                            "Smoke Check (Google)",
                            False,
                            "Invalid screenshot_base64 format",
                            {"screenshot_length": len(screenshot) if isinstance(screenshot, str) else 0}
                        )
                else:
                    self.log_test(
                        "Smoke Check (Google)",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Smoke Check (Google)",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Smoke Check (Google)",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_4_screenshot_full_retrieval(self):
        """Test 4: GET /api/automation/screenshot/{session_id}/full - Screenshot Full Retrieval"""
        print("\n🧪 Test 4: Screenshot Full Retrieval...")
        
        if not self.session_id:
            self.log_test(
                "Screenshot Full Retrieval",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/automation/screenshot/{self.session_id}/full",
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['screenshot_base64', 'screenshot_id', 'grid', 'vision', 'viewport']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    screenshot = data['screenshot_base64']
                    if isinstance(screenshot, str) and len(screenshot) > 100:
                        self.log_test(
                            "Screenshot Full Retrieval",
                            True,
                            f"Full screenshot retrieved ({len(screenshot)} chars)",
                            {
                                "screenshot_id": data['screenshot_id'],
                                "screenshot_length": len(screenshot),
                                "grid": data['grid'],
                                "viewport": data['viewport'],
                                "vision_array_length": len(data['vision']) if isinstance(data['vision'], list) else 0
                            }
                        )
                    else:
                        self.log_test(
                            "Screenshot Full Retrieval",
                            False,
                            "Invalid screenshot_base64 format",
                            {"screenshot_length": len(screenshot) if isinstance(screenshot, str) else 0}
                        )
                else:
                    self.log_test(
                        "Screenshot Full Retrieval",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Screenshot Full Retrieval",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Screenshot Full Retrieval",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_5_scene_snapshot(self):
        """Test 5: POST /api/automation/scene/snapshot - Scene Snapshot"""
        print("\n🧪 Test 5: Scene Snapshot...")
        
        if not self.session_id:
            self.log_test(
                "Scene Snapshot",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
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
                
                if 'scene' in data:
                    scene = data['scene']
                    required_scene_fields = ['viewport', 'url', 'http', 'antibot', 'elements', 'hints', 'ts']
                    missing_scene_fields = [field for field in required_scene_fields if field not in scene]
                    
                    if not missing_scene_fields:
                        self.scene_data = scene
                        self.log_test(
                            "Scene Snapshot",
                            True,
                            f"Scene snapshot captured with {len(scene.get('elements', []))} elements",
                            {
                                "scene_fields": list(scene.keys()),
                                "elements_count": len(scene.get('elements', [])),
                                "url": scene.get('url'),
                                "viewport": scene.get('viewport'),
                                "timestamp": scene.get('ts')
                            }
                        )
                    else:
                        self.log_test(
                            "Scene Snapshot",
                            False,
                            f"Scene object missing required fields: {missing_scene_fields}",
                            {"missing_scene_fields": missing_scene_fields, "scene_keys": list(scene.keys())}
                        )
                else:
                    self.log_test(
                        "Scene Snapshot",
                        False,
                        "Response missing 'scene' object",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Scene Snapshot",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Scene Snapshot",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_6_plan_generation(self):
        """Test 6: POST /api/automation/plan/decide - Plan Generation"""
        print("\n🧪 Test 6: Plan Generation...")
        
        if not self.session_id:
            self.log_test(
                "Plan Generation",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
        payload = {
            "session_id": self.session_id,
            "goal": {
                "site": "google.com",
                "task": "search"
            },
            "scene": None
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/plan/decide",
                json=payload,
                timeout=45
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'plan' in data:
                    plan = data['plan']
                    required_plan_fields = ['candidates', 'chosen', 'assumptions', 'risks']
                    missing_plan_fields = [field for field in required_plan_fields if field not in plan]
                    
                    if not missing_plan_fields:
                        self.log_test(
                            "Plan Generation",
                            True,
                            f"Plan generated with {len(plan.get('candidates', []))} candidates",
                            {
                                "candidates_count": len(plan.get('candidates', [])),
                                "chosen": plan.get('chosen'),
                                "assumptions_count": len(plan.get('assumptions', [])),
                                "risks_count": len(plan.get('risks', []))
                            }
                        )
                    else:
                        self.log_test(
                            "Plan Generation",
                            False,
                            f"Plan object missing required fields: {missing_plan_fields}",
                            {"missing_plan_fields": missing_plan_fields, "plan_keys": list(plan.keys())}
                        )
                else:
                    self.log_test(
                        "Plan Generation",
                        False,
                        "Response missing 'plan' object",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Plan Generation",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Plan Generation",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_7_click_cell(self):
        """Test 7: POST /api/automation/click-cell - Click Cell"""
        print("\n🧪 Test 7: Click Cell...")
        
        if not self.session_id:
            self.log_test(
                "Click Cell",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
        payload = {
            "session_id": self.session_id,
            "cell": "M12",
            "click_type": "single",
            "humanize": True
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/click-cell",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['screenshot_base64', 'dom_event']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    dom_event = data['dom_event']
                    if dom_event.get('cell') == "M12":
                        screenshot = data['screenshot_base64']
                        self.log_test(
                            "Click Cell",
                            True,
                            f"Cell M12 clicked successfully, new screenshot captured ({len(screenshot)} chars)",
                            {
                                "cell": dom_event.get('cell'),
                                "click_type": dom_event.get('click_type'),
                                "screenshot_length": len(screenshot)
                            }
                        )
                    else:
                        self.log_test(
                            "Click Cell",
                            False,
                            f"DOM event cell mismatch: expected M12, got {dom_event.get('cell')}",
                            {"expected_cell": "M12", "actual_cell": dom_event.get('cell')}
                        )
                else:
                    self.log_test(
                        "Click Cell",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Click Cell",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Click Cell",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_8_type_at_cell(self):
        """Test 8: POST /api/automation/type-at-cell - Type at Cell"""
        print("\n🧪 Test 8: Type at Cell...")
        
        if not self.session_id:
            self.log_test(
                "Type at Cell",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
        payload = {
            "session_id": self.session_id,
            "cell": "C7",
            "text": "test input"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/type-at-cell",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['screenshot_base64', 'dom_event']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    dom_event = data['dom_event']
                    if (dom_event.get('cell') == "C7" and 
                        dom_event.get('text') == "test input"):
                        screenshot = data['screenshot_base64']
                        self.log_test(
                            "Type at Cell",
                            True,
                            f"Text typed at cell C7 successfully, new screenshot captured ({len(screenshot)} chars)",
                            {
                                "cell": dom_event.get('cell'),
                                "text": dom_event.get('text'),
                                "screenshot_length": len(screenshot)
                            }
                        )
                    else:
                        self.log_test(
                            "Type at Cell",
                            False,
                            f"DOM event mismatch: expected C7/'test input', got {dom_event.get('cell')}/'{dom_event.get('text')}'",
                            {"expected": {"cell": "C7", "text": "test input"}, "actual": dom_event}
                        )
                else:
                    self.log_test(
                        "Type at Cell",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Type at Cell",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Type at Cell",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_9_hold_drag(self):
        """Test 9: POST /api/automation/hold-drag - Hold Drag (for CAPTCHA)"""
        print("\n🧪 Test 9: Hold Drag (for CAPTCHA)...")
        
        if not self.session_id:
            self.log_test(
                "Hold Drag",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
        payload = {
            "session_id": self.session_id,
            "from_cell": "A1",
            "to_cell": "D4",
            "speed": 1.0
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/hold-drag",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['screenshot_base64', 'dom_event']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    dom_event = data['dom_event']
                    if (dom_event.get('from') == "A1" and 
                        dom_event.get('to') == "D4"):
                        screenshot = data['screenshot_base64']
                        self.log_test(
                            "Hold Drag",
                            True,
                            f"Drag from A1 to D4 completed successfully, new screenshot captured ({len(screenshot)} chars)",
                            {
                                "from_cell": dom_event.get('from'),
                                "to_cell": dom_event.get('to'),
                                "speed": dom_event.get('speed'),
                                "screenshot_length": len(screenshot)
                            }
                        )
                    else:
                        self.log_test(
                            "Hold Drag",
                            False,
                            f"DOM event mismatch: expected A1→D4, got {dom_event.get('from')}→{dom_event.get('to')}",
                            {"expected": {"from": "A1", "to": "D4"}, "actual": dom_event}
                        )
                else:
                    self.log_test(
                        "Hold Drag",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Hold Drag",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Hold Drag",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_10_captcha_solve(self):
        """Test 10: POST /api/automation/captcha/solve - CAPTCHA Solve"""
        print("\n🧪 Test 10: CAPTCHA Solve...")
        
        if not self.session_id:
            self.log_test(
                "CAPTCHA Solve",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
        payload = {
            "session_id": self.session_id
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/captcha/solve",
                json=payload,
                timeout=60  # CAPTCHA solving can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'success' in data and 'message' in data:
                    # Note: May return "No CAPTCHA detected" if no CAPTCHA on page
                    message = data['message']
                    if "No CAPTCHA detected" in message or data.get('success') == True:
                        self.log_test(
                            "CAPTCHA Solve",
                            True,
                            f"CAPTCHA endpoint working: {message}",
                            {"success": data.get('success'), "message": message}
                        )
                    else:
                        self.log_test(
                            "CAPTCHA Solve",
                            False,
                            f"CAPTCHA solve failed: {message}",
                            {"success": data.get('success'), "message": message}
                        )
                else:
                    self.log_test(
                        "CAPTCHA Solve",
                        False,
                        "Response missing required fields (success, message)",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "CAPTCHA Solve",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "CAPTCHA Solve",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_11_selftest_run(self):
        """Test 11: POST /api/automation/selftest/run - SelfTest Run"""
        print("\n🧪 Test 11: SelfTest Run...")
        
        if not self.session_id:
            self.log_test(
                "SelfTest Run",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
        payload = {
            "session_id": self.session_id,
            "profile": "default"
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/selftest/run",
                json=payload,
                timeout=60  # SelfTest can take time
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'report' in data:
                    report = data['report']
                    required_report_fields = ['score', 'grade', 'issues', 'ip', 'fp']
                    missing_report_fields = [field for field in required_report_fields if field not in report]
                    
                    if not missing_report_fields:
                        score = report.get('score')
                        grade = report.get('grade')
                        
                        # Validate score is 0-100 and grade is green/yellow/red
                        if (isinstance(score, (int, float)) and 0 <= score <= 100 and 
                            grade in ['green', 'yellow', 'red']):
                            self.log_test(
                                "SelfTest Run",
                                True,
                                f"SelfTest completed: score={score}, grade={grade}",
                                {
                                    "score": score,
                                    "grade": grade,
                                    "issues_count": len(report.get('issues', [])),
                                    "ip_info": report.get('ip', {}),
                                    "fp_info": report.get('fp', {})
                                }
                            )
                        else:
                            self.log_test(
                                "SelfTest Run",
                                False,
                                f"Invalid score/grade: score={score}, grade={grade}",
                                {"score": score, "grade": grade, "score_type": type(score).__name__}
                            )
                    else:
                        self.log_test(
                            "SelfTest Run",
                            False,
                            f"Report missing required fields: {missing_report_fields}",
                            {"missing_report_fields": missing_report_fields, "report_keys": list(report.keys())}
                        )
                else:
                    self.log_test(
                        "SelfTest Run",
                        False,
                        "Response missing 'report' object",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "SelfTest Run",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "SelfTest Run",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_12_antibot_eval(self):
        """Test 12: POST /api/automation/antibot/eval - AntiBot Eval"""
        print("\n🧪 Test 12: AntiBot Eval...")
        
        # Use scene data from test 5 if available, otherwise use minimal scene
        scene_data = self.scene_data if self.scene_data else {
            "viewport": {"width": 1920, "height": 1080},
            "url": "https://google.com",
            "http": {"status": 200},
            "antibot": {"detected": False},
            "elements": [],
            "hints": [],
            "ts": int(time.time() * 1000)
        }
        
        payload = {
            "scene": scene_data,
            "history": []
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/antibot/eval",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if 'decision' in data:
                    decision = data['decision']
                    required_decision_fields = ['action', 'profile', 'backoff_ms']
                    missing_decision_fields = [field for field in required_decision_fields if field not in decision]
                    
                    if not missing_decision_fields:
                        action = decision.get('action')
                        valid_actions = ['continue', 'backoff', 'abort', 'wait_solver']
                        
                        if action in valid_actions:
                            self.log_test(
                                "AntiBot Eval",
                                True,
                                f"AntiBot evaluation completed: action={action}",
                                {
                                    "action": action,
                                    "profile": decision.get('profile'),
                                    "backoff_ms": decision.get('backoff_ms')
                                }
                            )
                        else:
                            self.log_test(
                                "AntiBot Eval",
                                False,
                                f"Invalid action: {action}, expected one of {valid_actions}",
                                {"action": action, "valid_actions": valid_actions}
                            )
                    else:
                        self.log_test(
                            "AntiBot Eval",
                            False,
                            f"Decision missing required fields: {missing_decision_fields}",
                            {"missing_decision_fields": missing_decision_fields, "decision_keys": list(decision.keys())}
                        )
                else:
                    self.log_test(
                        "AntiBot Eval",
                        False,
                        "Response missing 'decision' object",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "AntiBot Eval",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "AntiBot Eval",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_13_watchdog_init(self):
        """Test 13: POST /api/automation/watchdog/init - Watchdog Init"""
        print("\n🧪 Test 13: Watchdog Init...")
        
        if not self.session_id:
            self.log_test(
                "Watchdog Init",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
        payload = {
            "session_id": self.session_id,
            "goal": {
                "site": "test.com",
                "task": "register"
            }
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/watchdog/init",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if (data.get('state') == "Idle" and 
                    data.get('initialized') == True):
                    self.log_test(
                        "Watchdog Init",
                        True,
                        f"Watchdog initialized: state={data['state']}, initialized={data['initialized']}",
                        {"state": data['state'], "initialized": data['initialized']}
                    )
                else:
                    self.log_test(
                        "Watchdog Init",
                        False,
                        f"Invalid watchdog init response: state={data.get('state')}, initialized={data.get('initialized')}",
                        {"expected": {"state": "Idle", "initialized": True}, "actual": data}
                    )
            else:
                self.log_test(
                    "Watchdog Init",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Watchdog Init",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_14_watchdog_transition(self):
        """Test 14: POST /api/automation/watchdog/transition - Watchdog Transition"""
        print("\n🧪 Test 14: Watchdog Transition...")
        
        if not self.session_id:
            self.log_test(
                "Watchdog Transition",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
        payload = {
            "session_id": self.session_id,
            "next_state": "Snapshot",
            "data": None
        }
        
        try:
            response = self.session.post(
                f"{BACKEND_URL}/automation/watchdog/transition",
                json=payload,
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                
                if (data.get('ok') == True and 
                    data.get('state') == "Snapshot"):
                    self.log_test(
                        "Watchdog Transition",
                        True,
                        f"Watchdog transitioned: ok={data['ok']}, state={data['state']}",
                        {"ok": data['ok'], "state": data['state']}
                    )
                else:
                    self.log_test(
                        "Watchdog Transition",
                        False,
                        f"Invalid watchdog transition response: ok={data.get('ok')}, state={data.get('state')}",
                        {"expected": {"ok": True, "state": "Snapshot"}, "actual": data}
                    )
            else:
                self.log_test(
                    "Watchdog Transition",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Watchdog Transition",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_15_watchdog_status(self):
        """Test 15: GET /api/automation/watchdog/status/{session_id} - Watchdog Status"""
        print("\n🧪 Test 15: Watchdog Status...")
        
        if not self.session_id:
            self.log_test(
                "Watchdog Status",
                False,
                "No session_id available (smoke-check failed)",
                {"session_id": self.session_id}
            )
            return
        
        try:
            response = self.session.get(
                f"{BACKEND_URL}/automation/watchdog/status/{self.session_id}",
                timeout=15
            )
            
            if response.status_code == 200:
                data = response.json()
                
                required_fields = ['state', 'elapsed_ms', 'steps_count', 'scene_hash_counts', 'error_counts']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    self.log_test(
                        "Watchdog Status",
                        True,
                        f"Watchdog status retrieved: state={data['state']}, steps={data['steps_count']}",
                        {
                            "state": data['state'],
                            "elapsed_ms": data['elapsed_ms'],
                            "steps_count": data['steps_count'],
                            "scene_hash_counts": data['scene_hash_counts'],
                            "error_counts": data['error_counts']
                        }
                    )
                else:
                    self.log_test(
                        "Watchdog Status",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Watchdog Status",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Watchdog Status",
                False,
                f"Exception: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def run_all_tests(self):
        """Run all 15 automation endpoint tests in sequence"""
        print("🚀 Starting Comprehensive Automation Backend Testing - Phase 1")
        print("=" * 80)
        
        # Run tests in the specified order
        self.test_1_grid_configuration()
        self.test_2_session_creation_with_proxy()
        self.test_3_smoke_check_google()
        self.test_4_screenshot_full_retrieval()
        self.test_5_scene_snapshot()
        self.test_6_plan_generation()
        self.test_7_click_cell()
        self.test_8_type_at_cell()
        self.test_9_hold_drag()
        self.test_10_captcha_solve()
        self.test_11_selftest_run()
        self.test_12_antibot_eval()
        self.test_13_watchdog_init()
        self.test_14_watchdog_transition()
        self.test_15_watchdog_status()
        
        # Print summary
        print("\n" + "=" * 80)
        print("🏁 COMPREHENSIVE AUTOMATION TESTING COMPLETE")
        print("=" * 80)
        
        passed_tests = [result for result in self.test_results if result['success']]
        failed_tests = [result for result in self.test_results if not result['success']]
        
        print(f"\n📊 SUMMARY:")
        print(f"   Total Tests: {len(self.test_results)}")
        print(f"   ✅ Passed: {len(passed_tests)}")
        print(f"   ❌ Failed: {len(failed_tests)}")
        print(f"   Success Rate: {len(passed_tests)/len(self.test_results)*100:.1f}%")
        
        if failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for test in failed_tests:
                print(f"   - {test['test']}: {test['message']}")
        
        if passed_tests:
            print(f"\n✅ PASSED TESTS:")
            for test in passed_tests:
                print(f"   - {test['test']}: {test['message']}")
        
        return self.test_results

if __name__ == "__main__":
    tester = AutomationTester()
    results = tester.run_all_tests()