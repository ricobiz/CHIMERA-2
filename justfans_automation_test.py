#!/usr/bin/env python3
"""
JustFans.uno Browser Automation Flow Test
Tests the complete browser automation flow for justfans.uno registration
"""

import requests
import json
import time
from datetime import datetime

# Backend URL from frontend/.env
BACKEND_URL = "https://chimera-auto.preview.emergentagent.com/api"

class JustFansAutomationTester:
    def __init__(self):
        self.session = requests.Session()
        self.test_results = []
        
        # Test parameters from review request
        self.job_id = "72bf4eba-8047-4c0e-ad84-185959db3337"
        self.session_id = "2b8ab45b-2b71-48b9-9761-5967a287e590"
        self.target_url = "https://justfans.uno/register"
        self.task = "Navigate to https://justfans.uno/register and complete the registration form"
        
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
    
    def test_hook_log_status(self):
        """Test 1: Verify Hook Log Status - GET /api/hook/log"""
        print("\n🧪 Testing Hook Log Status...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/hook/log", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                
                # Check required fields
                required_fields = ['logs', 'status', 'job_id', 'result_ready', 'total_steps', 'timestamp', 'observation', 'session_id']
                missing_fields = [field for field in required_fields if field not in data]
                
                if not missing_fields:
                    # Verify job_id matches
                    if data.get('job_id') == self.job_id:
                        self.log_test(
                            "Hook Log - Job ID Match",
                            True,
                            f"Job ID matches: {data['job_id']}",
                            {"expected_job_id": self.job_id, "actual_job_id": data['job_id']}
                        )
                    else:
                        self.log_test(
                            "Hook Log - Job ID Mismatch",
                            False,
                            f"Job ID mismatch. Expected: {self.job_id}, Got: {data.get('job_id')}",
                            {"expected_job_id": self.job_id, "actual_job_id": data.get('job_id')}
                        )
                    
                    # Verify status is ACTIVE
                    if data.get('status') == 'ACTIVE':
                        self.log_test(
                            "Hook Log - Status Active",
                            True,
                            f"Status is ACTIVE as expected",
                            {"status": data['status']}
                        )
                    else:
                        self.log_test(
                            "Hook Log - Status Not Active",
                            False,
                            f"Status is {data.get('status')}, expected ACTIVE",
                            {"expected_status": "ACTIVE", "actual_status": data.get('status')}
                        )
                    
                    # Verify session_id matches
                    if data.get('session_id') == self.session_id:
                        self.log_test(
                            "Hook Log - Session ID Match",
                            True,
                            f"Session ID matches: {data['session_id']}",
                            {"expected_session_id": self.session_id, "actual_session_id": data['session_id']}
                        )
                    else:
                        self.log_test(
                            "Hook Log - Session ID Mismatch",
                            False,
                            f"Session ID mismatch. Expected: {self.session_id}, Got: {data.get('session_id')}",
                            {"expected_session_id": self.session_id, "actual_session_id": data.get('session_id')}
                        )
                    
                    # Verify logs array has entries (should be more than 30 steps)
                    logs = data.get('logs', [])
                    if isinstance(logs, list) and len(logs) > 30:
                        self.log_test(
                            "Hook Log - Sufficient Steps",
                            True,
                            f"Found {len(logs)} log entries (>30 as expected)",
                            {"log_count": len(logs), "expected_min": 30}
                        )
                    else:
                        self.log_test(
                            "Hook Log - Insufficient Steps",
                            False,
                            f"Found {len(logs) if isinstance(logs, list) else 0} log entries, expected >30",
                            {"log_count": len(logs) if isinstance(logs, list) else 0, "expected_min": 30}
                        )
                    
                    # Check observation.screenshot_base64 is not null
                    observation = data.get('observation', {})
                    screenshot_base64 = observation.get('screenshot_base64')
                    if screenshot_base64 and screenshot_base64 != "null":
                        self.log_test(
                            "Hook Log - Screenshot Present",
                            True,
                            f"Screenshot captured ({len(str(screenshot_base64))} chars)",
                            {"screenshot_length": len(str(screenshot_base64))}
                        )
                    else:
                        self.log_test(
                            "Hook Log - Screenshot Missing",
                            False,
                            "Screenshot is null or missing",
                            {"screenshot_base64": screenshot_base64}
                        )
                    
                    # Check observation.url contains "justfans.uno"
                    url = observation.get('url', '')
                    if 'justfans.uno' in url:
                        self.log_test(
                            "Hook Log - JustFans URL",
                            True,
                            f"URL contains justfans.uno: {url}",
                            {"url": url}
                        )
                    else:
                        self.log_test(
                            "Hook Log - Wrong URL",
                            False,
                            f"URL does not contain justfans.uno: {url}",
                            {"expected_domain": "justfans.uno", "actual_url": url}
                        )
                        
                else:
                    self.log_test(
                        "Hook Log - Missing Fields",
                        False,
                        f"Response missing required fields: {missing_fields}",
                        {"missing_fields": missing_fields, "response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Hook Log - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Hook Log - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_automation_scene_snapshot(self):
        """Test 2: Verify Automation Progress - POST /api/automation/scene/snapshot"""
        print("\n🧪 Testing Automation Scene Snapshot...")
        
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
                
                # Check required fields
                required_fields = ['scene']
                if 'scene' in data:
                    scene = data['scene']
                    scene_required_fields = ['url', 'elements']
                    scene_missing_fields = [field for field in scene_required_fields if field not in scene]
                    
                    if not scene_missing_fields:
                        # Verify scene.url is "https://justfans.uno/register"
                        scene_url = scene.get('url', '')
                        if scene_url == self.target_url:
                            self.log_test(
                                "Scene Snapshot - Correct URL",
                                True,
                                f"Scene URL matches target: {scene_url}",
                                {"expected_url": self.target_url, "actual_url": scene_url}
                            )
                        else:
                            self.log_test(
                                "Scene Snapshot - Wrong URL",
                                False,
                                f"Scene URL mismatch. Expected: {self.target_url}, Got: {scene_url}",
                                {"expected_url": self.target_url, "actual_url": scene_url}
                            )
                        
                        # Verify scene.elements array has form fields
                        elements = scene.get('elements', [])
                        if isinstance(elements, list) and len(elements) > 0:
                            self.log_test(
                                "Scene Snapshot - Elements Present",
                                True,
                                f"Found {len(elements)} elements in scene",
                                {"element_count": len(elements)}
                            )
                            
                            # Check if any textbox elements exist
                            textbox_elements = [elem for elem in elements if elem.get('type') == 'textbox' or 'input' in str(elem).lower()]
                            if textbox_elements:
                                self.log_test(
                                    "Scene Snapshot - Textbox Elements",
                                    True,
                                    f"Found {len(textbox_elements)} textbox/input elements",
                                    {"textbox_count": len(textbox_elements)}
                                )
                            else:
                                self.log_test(
                                    "Scene Snapshot - No Textbox Elements",
                                    False,
                                    "No textbox/input elements found in scene",
                                    {"elements_sample": elements[:3] if elements else []}
                                )
                        else:
                            self.log_test(
                                "Scene Snapshot - No Elements",
                                False,
                                "No elements found in scene",
                                {"elements": elements}
                            )
                    else:
                        self.log_test(
                            "Scene Snapshot - Missing Scene Fields",
                            False,
                            f"Scene missing required fields: {scene_missing_fields}",
                            {"missing_fields": scene_missing_fields, "scene_keys": list(scene.keys())}
                        )
                else:
                    self.log_test(
                        "Scene Snapshot - Missing Scene",
                        False,
                        "Response missing 'scene' field",
                        {"response_keys": list(data.keys())}
                    )
            else:
                self.log_test(
                    "Scene Snapshot - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Scene Snapshot - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_cognitive_loop_progression(self):
        """Test 3: Check Cognitive Loop - Verify logs show progression through cognitive stages"""
        print("\n🧪 Testing Cognitive Loop Progression...")
        
        try:
            response = self.session.get(f"{BACKEND_URL}/hook/log", timeout=15)
            
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                
                if isinstance(logs, list) and len(logs) > 0:
                    # Look for cognitive stages in logs
                    cognitive_stages = {
                        'scene_building': False,
                        'planning': False,
                        'action_execution': False
                    }
                    
                    error_count = 0
                    
                    for log_entry in logs:
                        log_text = str(log_entry).lower()
                        
                        # Check for scene building
                        if any(keyword in log_text for keyword in ['scene', 'snapshot', 'building', 'capture']):
                            cognitive_stages['scene_building'] = True
                        
                        # Check for planning
                        if any(keyword in log_text for keyword in ['plan', 'planning', 'decide', 'strategy']):
                            cognitive_stages['planning'] = True
                        
                        # Check for action execution
                        if any(keyword in log_text for keyword in ['action', 'execute', 'click', 'type', 'fill']):
                            cognitive_stages['action_execution'] = True
                        
                        # Check for errors
                        if any(keyword in log_text for keyword in ['error', 'failed', 'exception']):
                            error_count += 1
                    
                    # Evaluate cognitive loop progression
                    stages_found = sum(cognitive_stages.values())
                    if stages_found >= 2:
                        self.log_test(
                            "Cognitive Loop - Stages Present",
                            True,
                            f"Found {stages_found}/3 cognitive stages in logs",
                            {"stages_found": cognitive_stages, "total_logs": len(logs)}
                        )
                    else:
                        self.log_test(
                            "Cognitive Loop - Insufficient Stages",
                            False,
                            f"Only found {stages_found}/3 cognitive stages",
                            {"stages_found": cognitive_stages, "total_logs": len(logs)}
                        )
                    
                    # Check error rate
                    error_rate = error_count / len(logs) if len(logs) > 0 else 0
                    if error_rate < 0.1:  # Less than 10% error rate
                        self.log_test(
                            "Cognitive Loop - Low Error Rate",
                            True,
                            f"Error rate: {error_rate:.2%} ({error_count}/{len(logs)})",
                            {"error_count": error_count, "total_logs": len(logs), "error_rate": error_rate}
                        )
                    else:
                        self.log_test(
                            "Cognitive Loop - High Error Rate",
                            False,
                            f"High error rate: {error_rate:.2%} ({error_count}/{len(logs)})",
                            {"error_count": error_count, "total_logs": len(logs), "error_rate": error_rate}
                        )
                        
                else:
                    self.log_test(
                        "Cognitive Loop - No Logs",
                        False,
                        "No logs available for cognitive loop analysis",
                        {"logs": logs}
                    )
            else:
                self.log_test(
                    "Cognitive Loop - HTTP Error",
                    False,
                    f"HTTP {response.status_code}: {response.text}",
                    {"status_code": response.status_code}
                )
                
        except Exception as e:
            self.log_test(
                "Cognitive Loop - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def test_real_time_progress_monitoring(self):
        """Test 4: Monitor Real-time Progress - Call /api/hook/log multiple times"""
        print("\n🧪 Testing Real-time Progress Monitoring...")
        
        progress_data = []
        
        try:
            # Call hook/log 4 times with 2 second delays
            for i in range(4):
                print(f"   Progress check {i+1}/4...")
                
                response = self.session.get(f"{BACKEND_URL}/hook/log", timeout=15)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    progress_entry = {
                        "check_number": i + 1,
                        "timestamp": datetime.now().isoformat(),
                        "total_steps": data.get('total_steps', 0),
                        "logs_count": len(data.get('logs', [])),
                        "screenshot_id": data.get('observation', {}).get('screenshot_id'),
                        "status": data.get('status')
                    }
                    
                    progress_data.append(progress_entry)
                    
                    if i < 3:  # Don't sleep after the last check
                        time.sleep(2)
                else:
                    self.log_test(
                        f"Real-time Progress - Check {i+1} Failed",
                        False,
                        f"HTTP {response.status_code}: {response.text}",
                        {"check_number": i+1, "status_code": response.status_code}
                    )
                    return
            
            # Analyze progress data
            if len(progress_data) >= 2:
                # Check if step numbers are increasing
                step_increases = 0
                screenshot_changes = 0
                
                for i in range(1, len(progress_data)):
                    prev_steps = progress_data[i-1]['total_steps']
                    curr_steps = progress_data[i]['total_steps']
                    
                    if curr_steps > prev_steps:
                        step_increases += 1
                    
                    prev_screenshot = progress_data[i-1]['screenshot_id']
                    curr_screenshot = progress_data[i]['screenshot_id']
                    
                    if prev_screenshot != curr_screenshot and curr_screenshot:
                        screenshot_changes += 1
                
                # Evaluate progress
                if step_increases > 0:
                    self.log_test(
                        "Real-time Progress - Step Progression",
                        True,
                        f"Steps increased {step_increases} times during monitoring",
                        {"step_increases": step_increases, "progress_data": progress_data}
                    )
                else:
                    self.log_test(
                        "Real-time Progress - No Step Progression",
                        False,
                        "No step increases detected during monitoring",
                        {"step_increases": step_increases, "progress_data": progress_data}
                    )
                
                if screenshot_changes > 0:
                    self.log_test(
                        "Real-time Progress - Screenshot Updates",
                        True,
                        f"Screenshot changed {screenshot_changes} times (indicates page updates)",
                        {"screenshot_changes": screenshot_changes, "progress_data": progress_data}
                    )
                else:
                    self.log_test(
                        "Real-time Progress - No Screenshot Updates",
                        False,
                        "No screenshot changes detected (may indicate stuck automation)",
                        {"screenshot_changes": screenshot_changes, "progress_data": progress_data}
                    )
                
                # Check if automation is still active
                final_status = progress_data[-1]['status']
                if final_status == 'ACTIVE':
                    self.log_test(
                        "Real-time Progress - Still Active",
                        True,
                        "Automation is still ACTIVE after monitoring period",
                        {"final_status": final_status}
                    )
                else:
                    self.log_test(
                        "Real-time Progress - Not Active",
                        False,
                        f"Automation status changed to {final_status}",
                        {"final_status": final_status}
                    )
            else:
                self.log_test(
                    "Real-time Progress - Insufficient Data",
                    False,
                    "Could not collect sufficient progress data",
                    {"progress_data": progress_data}
                )
                
        except Exception as e:
            self.log_test(
                "Real-time Progress - Exception",
                False,
                f"Unexpected error: {str(e)}",
                {"error_type": type(e).__name__}
            )
    
    def generate_summary_report(self):
        """Generate a comprehensive summary report"""
        print("\n" + "="*80)
        print("🎯 JUSTFANS.UNO AUTOMATION FLOW TEST SUMMARY")
        print("="*80)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result['success'])
        failed_tests = total_tests - passed_tests
        
        print(f"\n📊 OVERALL RESULTS:")
        print(f"   Total Tests: {total_tests}")
        print(f"   Passed: {passed_tests} ✅")
        print(f"   Failed: {failed_tests} ❌")
        print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print(f"\n🔍 TEST PARAMETERS:")
        print(f"   Job ID: {self.job_id}")
        print(f"   Session ID: {self.session_id}")
        print(f"   Target URL: {self.target_url}")
        print(f"   Task: {self.task}")
        
        # Show last 15 log entries if available
        print(f"\n📋 LAST 15 LOG ENTRIES:")
        try:
            response = self.session.get(f"{BACKEND_URL}/hook/log", timeout=15)
            if response.status_code == 200:
                data = response.json()
                logs = data.get('logs', [])
                
                if logs:
                    recent_logs = logs[-15:] if len(logs) > 15 else logs
                    for i, log_entry in enumerate(recent_logs, 1):
                        print(f"   {i:2d}. {str(log_entry)[:100]}...")
                else:
                    print("   No logs available")
            else:
                print(f"   Could not retrieve logs (HTTP {response.status_code})")
        except Exception as e:
            print(f"   Error retrieving logs: {str(e)}")
        
        # Identify blocking issues
        print(f"\n🚨 BLOCKING ISSUES:")
        blocking_issues = [result for result in self.test_results if not result['success']]
        
        if blocking_issues:
            for issue in blocking_issues:
                print(f"   ❌ {issue['test']}: {issue['message']}")
        else:
            print("   ✅ No blocking issues identified")
        
        # Automation status assessment
        print(f"\n🤖 AUTOMATION STATUS ASSESSMENT:")
        
        # Check if automation is progressing or stuck
        hook_log_tests = [r for r in self.test_results if 'Hook Log' in r['test']]
        progress_tests = [r for r in self.test_results if 'Progress' in r['test']]
        
        if any(t['success'] for t in hook_log_tests) and any(t['success'] for t in progress_tests):
            print("   ✅ Automation appears to be progressing normally")
        elif any(t['success'] for t in hook_log_tests):
            print("   ⚠️  Automation is active but progress unclear")
        else:
            print("   ❌ Automation appears to be stuck or not running")
        
        print("\n" + "="*80)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": (passed_tests/total_tests)*100,
            "blocking_issues": len(blocking_issues),
            "test_results": self.test_results
        }
    
    def run_all_tests(self):
        """Run all JustFans automation tests"""
        print("🚀 Starting JustFans.uno Browser Automation Flow Tests...")
        print(f"Target: {self.target_url}")
        print(f"Job ID: {self.job_id}")
        print(f"Session ID: {self.session_id}")
        
        # Run all test methods
        self.test_hook_log_status()
        self.test_automation_scene_snapshot()
        self.test_cognitive_loop_progression()
        self.test_real_time_progress_monitoring()
        
        # Generate summary report
        return self.generate_summary_report()

def main():
    """Main test execution"""
    tester = JustFansAutomationTester()
    summary = tester.run_all_tests()
    
    # Exit with appropriate code
    if summary['failed_tests'] == 0:
        print("\n🎉 All tests passed!")
        exit(0)
    else:
        print(f"\n💥 {summary['failed_tests']} test(s) failed!")
        exit(1)

if __name__ == "__main__":
    main()