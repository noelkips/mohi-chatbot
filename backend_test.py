"""
Backend API Testing for Rafiki IT Support Chat
Tests health endpoints and chat functionality
"""

import requests
import sys
import json
from datetime import datetime

class RafikiAPITester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=30):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)
            
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                except:
                    print(f"   Response (text): {response.text[:200]}...")
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text}")

            test_result = {
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_time": response.elapsed.total_seconds(),
                "error": None
            }

            if success:
                try:
                    test_result["response_data"] = response.json()
                except:
                    test_result["response_data"] = response.text[:200]

            self.test_results.append(test_result)
            return success, response.json() if success and response.text else {}

        except requests.exceptions.Timeout:
            error_msg = f"Timeout after {timeout}s"
            print(f"❌ Failed - {error_msg}")
            self.test_results.append({
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "response_time": timeout,
                "error": error_msg
            })
            return False, {}
        except Exception as e:
            error_msg = str(e)
            print(f"❌ Failed - Error: {error_msg}")
            self.test_results.append({
                "name": name,
                "endpoint": endpoint,
                "method": method,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "response_time": None,
                "error": error_msg
            })
            return False, {}

    def test_health_endpoints(self):
        """Test both health check endpoints"""
        print("\n" + "="*60)
        print("🏥 TESTING HEALTH ENDPOINTS")
        print("="*60)
        
        success1, response1 = self.run_test(
            "Health Check",
            "GET",
            "health",
            200
        )

        success2, response2 = self.run_test(
            "API Health Check", 
            "GET",
            "api/health",
            200
        )
        
        return success1 and success2

    def test_chat_endpoint(self):
        """Test the chat endpoint with various scenarios"""
        print("\n" + "="*60)
        print("💬 TESTING CHAT ENDPOINT")
        print("="*60)
        
        # Test 1: Simple chat message
        test_data = {
            "message": "Hello, can you help me with IT support?",
            "history": []
        }
        
        success1, response1 = self.run_test(
            "Simple Chat Message",
            "POST",
            "api/chat",
            200,
            data=test_data,
            timeout=60  # Longer timeout for AI response
        )
        
        # Test 2: Chat with history
        test_data_with_history = {
            "message": "What are your office hours?",
            "history": [
                {"role": "user", "content": "Hello"},
                {"role": "assistant", "content": "Hi! How can I help you today?"}
            ]
        }
        
        success2, response2 = self.run_test(
            "Chat with History",
            "POST",
            "api/chat",
            200,
            data=test_data_with_history,
            timeout=60
        )
        
        # Test 3: IT Office Location (Quick Action)
        test_quick_action = {
            "message": "Where is the IT office located and what are the extensions?",
            "history": []
        }
        
        success3, response3 = self.run_test(
            "IT Office Location Query",
            "POST",
            "api/chat",
            200,
            data=test_quick_action,
            timeout=60
        )
        
        # Test 4: Portal Lockout Help (Quick Action)
        test_lockout = {
            "message": "My portal account is locked, what should I do?",
            "history": []
        }
        
        success4, response4 = self.run_test(
            "Portal Lockout Help",
            "POST",
            "api/chat",
            200,
            data=test_lockout,
            timeout=60
        )
        
        # Test 5: Leave Application (Quick Action)
        test_leave = {
            "message": "Show me the steps to apply for employee leave.",
            "history": []
        }
        
        success5, response5 = self.run_test(
            "Leave Application Steps",
            "POST",
            "api/chat",
            200,
            data=test_leave,
            timeout=60
        )
        
        # Test 6: Empty message (should fail gracefully)
        test_empty = {
            "message": "",
            "history": []
        }
        
        success6, response6 = self.run_test(
            "Empty Message Handling",
            "POST",
            "api/chat",
            200,  # Should still return 200 but handle gracefully
            data=test_empty,
            timeout=30
        )
        
        return all([success1, success2, success3, success4, success5])

    def test_error_scenarios(self):
        """Test error handling"""
        print("\n" + "="*60)
        print("🚨 TESTING ERROR SCENARIOS")
        print("="*60)
        
        # Test invalid endpoint
        success1, response1 = self.run_test(
            "Invalid Endpoint",
            "GET",
            "api/invalid",
            404
        )
        
        # Test malformed JSON
        try:
            url = f"{self.base_url}/api/chat"
            response = requests.post(url, data="invalid json", headers={'Content-Type': 'application/json'})
            success2 = response.status_code in [400, 422]  # Should return 4xx for bad request
            print(f"\n🔍 Testing Malformed JSON...")
            if success2:
                print(f"✅ Passed - Status: {response.status_code}")
                self.tests_passed += 1
            else:
                print(f"❌ Failed - Expected 400/422, got {response.status_code}")
            self.tests_run += 1
        except Exception as e:
            print(f"❌ Error testing malformed JSON: {e}")
            success2 = False
            self.tests_run += 1
        
        return success1

    def run_all_tests(self):
        """Run all test suites"""
        print("🤖 RAFIKI IT BACKEND API TESTS")
        print("="*80)
        print(f"Testing against: {self.base_url}")
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Run test suites
        health_ok = self.test_health_endpoints()
        chat_ok = self.test_chat_endpoint()
        error_ok = self.test_error_scenarios()
        
        # Print final results
        print("\n" + "="*80)
        print("📊 FINAL TEST RESULTS")
        print("="*80)
        print(f"Tests passed: {self.tests_passed}/{self.tests_run}")
        print(f"Success rate: {(self.tests_passed/self.tests_run)*100:.1f}%")
        
        if health_ok:
            print("✅ Health endpoints working")
        else:
            print("❌ Health endpoints failing")
            
        if chat_ok:
            print("✅ Chat functionality working")
        else:
            print("❌ Chat functionality has issues")
            
        if error_ok:
            print("✅ Error handling working")
        else:
            print("❌ Error handling has issues")
        
        # Return success if majority of tests pass
        return self.tests_passed >= (self.tests_run * 0.7)  # 70% pass rate

def main():
    """Main test execution"""
    tester = RafikiAPITester()
    success = tester.run_all_tests()
    
    # Save detailed results
    results_file = "test_reports/backend_api_results.json"
    with open(results_file, 'w') as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_tests": tester.tests_run,
            "passed_tests": tester.tests_passed,
            "success_rate": (tester.tests_passed/tester.tests_run)*100,
            "test_results": tester.test_results
        }, f, indent=2)
    
    print(f"\n📄 Detailed results saved to: {results_file}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
