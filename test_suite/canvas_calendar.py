"""
Canvas Calendar Sync Test Case Implementation
Tests the Canvas assignment synchronization in VT Calendar application.

Test Case: Canvas Calendar Sync Check
Preconditions: Previously connected Canvas account
Steps:
1. Navigate to the calendar screen
2. Hit sync with Canvas button
Expected Results: New Canvas assignments appear on calendar

The tested behavior is implemented in:
- Backend: app.py /api/canvas/link endpoint (lines 205-248)
- Backend: canvas_test.py (Canvas API integration logic)
- Frontend: auth.js handleSync() (lines 452-474)
AI use:
Claude Sonnet was used to better understand the requirements and set up the test case structure using the following prompt:
Implement a skeleton for the following testcase:
Canvas Calendar Sync Check
Preconditions:
Previously connected Canvas account
Steps:
1. Navigate to the calendar screen
2. Hit sync with Canvas button
Expected Results - New Canvas assignments appear on calendar

The tested behavior is implemented in canvas_test.py
Explain what information is relevant to determine pass or failure. Where do you get that information from? How do you get it?
"""

import unittest
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
import requests
import json


class CanvasSyncTest(unittest.TestCase):
    """Test case for Canvas calendar synchronization"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment once before all tests"""
        cls.driver = webdriver.Chrome()
        cls.driver.maximize_window()
        cls.base_url = "http://127.0.0.1:3001"
        cls.api_url = "http://127.0.0.1:3001/api"
        cls.wait = WebDriverWait(cls.driver, 10)
        
    @classmethod
    def tearDownClass(cls):
        """Clean up after all tests"""
        cls.driver.quit()
    
    def test_canvas_sync_success(self):
        
        
        print("\n" + "="*70)
        print("CANVAS CALENDAR SYNC TEST")
        print("="*70 + "\n")
        
        # Precondition: Ensure Canvas account is connected
        print("Precondition: Verify Canvas account connected")
        self._ensure_canvas_connected()
        
        # Step 1: Navigate to the calendar screen
        print("\nStep 1: Navigate to calendar screen")
        self.driver.get(f"{self.base_url}/auth.html")
        
        # Wait for dashboard to load
        dashboard = self.wait.until(
            EC.visibility_of_element_located((By.ID, "dashboardSection"))
        )
        self.assertTrue(dashboard.is_displayed(), "Dashboard not visible")
        print("✓ Calendar dashboard loaded")
        
        # Capture initial state
        print("\n--- Capturing Pre-Sync State ---")
        initial_event_count = self._count_calendar_events()
        initial_events = self._get_displayed_events()
        
        print(f"Initial event count: {initial_event_count}")
        print(f"Initial events captured: {len(initial_events)} events")
        
        if initial_events:
            print("Sample initial events:")
            for i, event in enumerate(initial_events[:3]):
                print(f"  {i+1}. {event['title']} - {event['source']}")
        
        # Step 2: Hit sync with Canvas button
        print("\n--- Step 2: Click Sync Button ---")
        sync_result = self._click_sync_button()
        
        if not sync_result:
            self.fail("Failed to click sync button")
        
        # Wait for sync to complete (check for notification or loading state)
        print("\n--- Waiting for Sync to Complete ---")
        sync_success = self._wait_for_sync_completion()
        
        # Expected Result: Verify new Canvas assignments appear
        print("\n" + "="*70)
        print("VERIFYING EXPECTED RESULTS")
        print("="*70 + "\n")
        
        # Give a moment for UI to update
        time.sleep(2)
        
        # Capture post-sync state
        print("--- Capturing Post-Sync State ---")
        final_event_count = self._count_calendar_events()
        final_events = self._get_displayed_events()
        
        print(f"Final event count: {final_event_count}")
        print(f"Final events captured: {len(final_events)} events")
        
        # Calculate new events
        new_event_count = final_event_count - initial_event_count
        print(f"\nNew events added: {new_event_count}")
        
        # Verify new Canvas assignments appeared
        canvas_events = [e for e in final_events if e['source'] == 'Canvas']
        print(f"Total Canvas events: {len(canvas_events)}")
        
        if canvas_events:
            print("\nCanvas assignments found:")
            for i, event in enumerate(canvas_events[:5]):
                print(f"  {i+1}. {event['title']}")
                print(f"     Due: {event['due_date']}")
                print(f"     Course: {event.get('course_name', 'N/A')}")
        
        # Verify data quality
        print("\n--- Verifying Data Quality ---")
        data_quality_pass = self._verify_event_data_quality(canvas_events)
        
        # Verify via API
        print("\n--- Verifying via API ---")
        api_verification_pass = self._verify_sync_via_api()
        
        # Determine overall test result
        print("\n" + "="*70)
        print("TEST RESULT DETERMINATION")
        print("="*70 + "\n")
        
        checks = {
            "Sync button clicked successfully": sync_result,
            "Sync completion detected": sync_success,
            "New events appeared": new_event_count > 0 or len(canvas_events) > 0,
            "Canvas events found": len(canvas_events) > 0,
            "Event data quality verified": data_quality_pass,
            "API verification passed": api_verification_pass
        }
        
        for check_name, passed in checks.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {check_name}")
        
        all_passed = all(checks.values())
        
        print("\n" + "="*70)
        if all_passed:
            print("OVERALL TEST RESULT: PASS ✓")
            print("Canvas calendar sync successful - assignments synced correctly")
        else:
            print("OVERALL TEST RESULT: FAIL ✗")
            failed_checks = [name for name, passed in checks.items() if not passed]
            print(f"Failed checks: {', '.join(failed_checks)}")
        print("="*70 + "\n")
        
        # Assert for unittest framework
        self.assertTrue(all_passed, f"Canvas sync test failed: {failed_checks if not all_passed else ''}")
    
    def _ensure_canvas_connected(self):
        
        # Login first
        self.driver.get(f"{self.base_url}/auth.html")
        
        # Check if already logged in with Canvas connected
        try:
            # Execute JavaScript to check localStorage
            canvas_token = self.driver.execute_script(
                "return localStorage.getItem('canvasToken');"
            )
            user_id = self.driver.execute_script(
                "return localStorage.getItem('userId');"
            )
            
            if canvas_token and user_id:
                print(f"✓ Canvas already connected (User ID: {user_id})")
                return
        except:
            pass
        
        # If not connected, perform login and Canvas link
        print("⚠ Canvas not connected, setting up precondition...")
        self._perform_login_and_canvas_link()
        print("✓ Canvas connection established")
    
    def _perform_login_and_canvas_link(self):
        """Helper to login and link Canvas account"""
        # Register/login
        try:
            register_tab = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".tab-btn[data-tab='register']"))
            )
            register_tab.click()
            time.sleep(0.5)
            
            test_email = f"synctest{int(time.time())}@vt.edu"
            test_password = "TestPass123"
            
            email_input = self.driver.find_element(By.ID, "registerEmail")
            password_input = self.driver.find_element(By.ID, "registerPassword")
            
            email_input.send_keys(test_email)
            password_input.send_keys(test_password)
            
            register_btn = self.driver.find_element(
                By.CSS_SELECTOR, "#registerFormContent button[type='submit']"
            )
            register_btn.click()
            time.sleep(1)
            
            # Login
            login_tab = self.wait.until(
                EC.element_to_be_clickable((By.CSS_SELECTOR, ".tab-btn[data-tab='login']"))
            )
            login_tab.click()
            time.sleep(0.5)
            
            login_email = self.driver.find_element(By.ID, "loginEmail")
            login_password = self.driver.find_element(By.ID, "loginPassword")
            
            login_email.send_keys(test_email)
            login_password.send_keys(test_password)
            
            login_btn = self.driver.find_element(
                By.CSS_SELECTOR, "#loginFormContent button[type='submit']"
            )
            login_btn.click()
            
            # Wait for dashboard
            self.wait.until(
                EC.visibility_of_element_located((By.ID, "dashboardSection"))
            )
        except:
            pass
        
        # Link Canvas
        try:
            link_canvas_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "linkCanvasBtn"))
            )
            link_canvas_btn.click()
            time.sleep(1)
            
            canvas_token_input = self.wait.until(
                EC.presence_of_element_located((By.ID, "canvasToken"))
            )
            
            # Use test token
            test_canvas_token = "test_canvas_token_sync"
            canvas_token_input.send_keys(test_canvas_token)
            
            link_submit = self.driver.find_element(
                By.CSS_SELECTOR, "#linkCanvasForm button[type='submit']"
            )
            link_submit.click()
            
            time.sleep(2)
        except Exception as e:
            print(f"⚠ Canvas link warning: {str(e)}")
    
    def _count_calendar_events(self):
        
        try:
            events_list = self.driver.find_element(By.ID, "eventsList")
            event_items = events_list.find_elements(By.CLASS_NAME, "event-item")
            
            # Filter out empty state
            actual_events = [
                e for e in event_items 
                if "empty" not in e.get_attribute("class")
            ]
            
            return len(actual_events)
        except NoSuchElementException:
            return 0
    
    def _get_displayed_events(self):
        
        events = []
        try:
            events_list = self.driver.find_element(By.ID, "eventsList")
            event_items = events_list.find_elements(By.CLASS_NAME, "event-item")
            
            for item in event_items:
                # Skip empty state
                if "empty" in item.get_attribute("class"):
                    continue
                
                try:
                    title_elem = item.find_element(By.CLASS_NAME, "event-title")
                    date_elem = item.find_element(By.CLASS_NAME, "event-date")
                    source_elem = item.find_element(By.CLASS_NAME, "event-source")
                    
                    # Course name is optional
                    try:
                        course_elem = item.find_element(By.CLASS_NAME, "event-course")
                        course_name = course_elem.text
                    except NoSuchElementException:
                        course_name = None
                    
                    event = {
                        'title': title_elem.text,
                        'due_date': date_elem.text,
                        'source': source_elem.text,
                        'course_name': course_name
                    }
                    events.append(event)
                except Exception as e:
                    print(f"⚠ Error parsing event: {e}")
                    continue
            
        except NoSuchElementException:
            pass
        
        return events
    
    def _click_sync_button(self):
        
        try:
            sync_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "syncBtn"))
            )
            
            print(f"✓ Sync button found and clickable")
            sync_btn.click()
            print(f"✓ Sync button clicked")
            
            return True
            
        except TimeoutException:
            print("✗ Sync button not found or not clickable")
            return False
        except Exception as e:
            print(f"✗ Error clicking sync button: {str(e)}")
            return False
    
    def _wait_for_sync_completion(self):
    
        try:
            # First wait for "Syncing..." notification
            print("⏳ Waiting for sync to start...")
            time.sleep(1)
            
            # Wait for completion notification (success or error)
            print("⏳ Waiting for sync completion notification...")
            notification = WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.CLASS_NAME, "notification"))
            )
            
            message = notification.text
            notification_classes = notification.get_attribute("class")
            
            print(f"Notification received: '{message}'")
            
            # Check if success
            if "success" in notification_classes:
                if any(keyword in message.lower() for keyword in ["sync", "canvas", "assignment"]):
                    print("✓ Sync completed successfully")
                    return True
            
            # Check if error
            if "error" in notification_classes:
                print(f"✗ Sync failed with error: {message}")
                return False
            
            # Ambiguous result
            print(f"⚠ Unexpected notification type: {notification_classes}")
            return False
            
        except TimeoutException:
            print("✗ Sync completion notification did not appear (timeout)")
            return False
    
    def _verify_event_data_quality(self, canvas_events):
        
        if not canvas_events:
            print("⚠ No Canvas events to verify")
            return False
        
        print(f"Verifying data quality for {len(canvas_events)} Canvas events...")
        
        valid_count = 0
        invalid_count = 0
        
        for i, event in enumerate(canvas_events):
            # Check required fields
            has_title = bool(event.get('title', '').strip())
            has_due_date = bool(event.get('due_date', '').strip())
            has_source = event.get('source') == 'Canvas'
            
            is_valid = has_title and has_due_date and has_source
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                print(f"  ✗ Event {i+1} missing required data:")
                if not has_title:
                    print("    - Missing title")
                if not has_due_date:
                    print("    - Missing due date")
                if not has_source:
                    print(f"    - Wrong source: {event.get('source')}")
        
        print(f"Valid events: {valid_count}/{len(canvas_events)}")
        
        if invalid_count > 0:
            print(f"⚠ {invalid_count} events have data quality issues")
        
        return valid_count > 0 and invalid_count == 0
    
    def _verify_sync_via_api(self):

        try:
            # Get user ID from browser
            user_id = self.driver.execute_script(
                "return localStorage.getItem('userId');"
            )
            
            if not user_id:
                print("✗ Could not get user ID from localStorage")
                return False
            
            print(f"Querying API for user {user_id}...")
            
            # Query API
            response = requests.get(
                f"{self.api_url}/calendar/events",
                params={'userId': user_id}
            )
            
            if response.status_code != 200:
                print(f"✗ API returned status code {response.status_code}")
                return False
            
            data = response.json()
            events = data.get('events', [])
            
            print(f"API returned {len(events)} total events")
            
            # Count Canvas events
            canvas_events = [e for e in events if e.get('source') == 'Canvas']
            print(f"Found {len(canvas_events)} Canvas events via API")
            
            if canvas_events:
                print("Sample Canvas events from API:")
                for i, event in enumerate(canvas_events[:3]):
                    print(f"  {i+1}. {event.get('title')} - Course: {event.get('course_name', 'N/A')}")
                
                return True
            else:
                print("⚠ No Canvas events found in API response")
                return False
            
        except requests.RequestException as e:
            print(f"✗ API request failed: {str(e)}")
            return False
        except Exception as e:
            print(f"✗ API verification error: {str(e)}")
            return False


def run_detailed_sync_test():
    
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(CanvasSyncTest)
    
    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print comprehensive summary
    print("\n" + "="*70)
    print("CANVAS SYNC TEST EXECUTION SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    
    if result.failures:
        print("\nFailure Details:")
        for test, traceback in result.failures:
            print(f"  {test}: {traceback}")
    
    if result.errors:
        print("\nError Details:")
        for test, traceback in result.errors:
            print(f"  {test}: {traceback}")
    
    print("="*70 + "\n")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    # Run comprehensive sync test
    success = run_detailed_sync_test()
    
    # Exit with appropriate code
    exit(0 if success else 1)