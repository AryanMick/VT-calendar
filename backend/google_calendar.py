
"""
Google Calendar Sync Test Case Implementation
Tests the Google Calendar event synchronization in VT Calendar application.

Test Case: Google Calendar Sync Check
Preconditions: Previously connected Google account
Steps:
1. Navigate to the calendar screen
2. Hit sync button
Expected Results: Google calendar events appear on calendar

The tested behavior is implemented in:
- Backend: google_calendar.py (Google Calendar API integration logic)
- Backend: app.py (would need Google sync endpoint - currently not implemented)
- Frontend: auth.js handleSync() (lines 452-474)

NOTE: The current codebase does NOT have full Google Calendar sync implementation.
This test demonstrates what would need to be tested if it were implemented.

AI use: Claude Sonnet was used to better understand the requirements and set up the test case structure using the following prompt:
Implement a skeleton for the following testcase:
Google calendar Sync check
Preconditions:
Previously connected Google account
Steps:
1. Navigate to the calendar screen
2. Hit sync with Canvas button
Expected Results - Google calendar events appear on calendar

The tested behavior is implemented in google_calendar.py
Explain what information is relevant to determine pass or failure. Where do you get that information from? How do you get it?
"""

import unittest
import json
import time
import requests
import os
from datetime import datetime, timezone, timedelta
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException


class GoogleCalendarSyncTest(unittest.TestCase):
    """Test case for Google Calendar synchronization"""
    
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
    
    def test_google_calendar_sync_success(self):
        
        print("\n" + "="*70)
        print("GOOGLE CALENDAR SYNC TEST")
        print("="*70 + "\n")
        
        # Precondition: Ensure Google account is connected
        print("Precondition: Verify Google account connected")
        google_connected = self._ensure_google_connected()
        
        if not google_connected:
            print("\n" + "="*70)
            print("TEST RESULT: SKIPPED")
            print("Google Calendar sync not fully implemented in backend")
            print("See test comments for implementation requirements")
            print("="*70 + "\n")
            self.skipTest("Google Calendar sync endpoint not implemented in app.py")
        
        # Step 1: Navigate to the calendar screen
        print("\nStep 1: Navigate to calendar screen")
        self.driver.get(f"{self.base_url}/auth.html")
        
        dashboard = self.wait.until(
            EC.visibility_of_element_located((By.ID, "dashboardSection"))
        )
        self.assertTrue(dashboard.is_displayed(), "Dashboard not visible")
        print("✓ Calendar dashboard loaded")
        
        # Capture initial state
        print("\n--- Capturing Pre-Sync State ---")
        initial_event_count = self._count_calendar_events()
        initial_events = self._get_displayed_events()
        initial_google_events = [e for e in initial_events if e['source'] == 'Google']
        
        print(f"Initial total events: {initial_event_count}")
        print(f"Initial Google events: {len(initial_google_events)}")
        
        # Step 2: Hit sync button
        print("\n--- Step 2: Click Sync Button ---")
        sync_result = self._click_sync_button()
        
        if not sync_result:
            self.fail("Failed to click sync button")
        
        # Wait for sync to complete
        print("\n--- Waiting for Sync to Complete ---")
        sync_success = self._wait_for_google_sync_completion()
        
        # Expected Result: Verify Google calendar events appear
        print("\n" + "="*70)
        print("VERIFYING EXPECTED RESULTS")
        print("="*70 + "\n")
        
        # Wait for UI to update
        time.sleep(2)
        
        # Capture post-sync state
        print("--- Capturing Post-Sync State ---")
        final_event_count = self._count_calendar_events()
        final_events = self._get_displayed_events()
        final_google_events = [e for e in final_events if e['source'] == 'Google']
        
        print(f"Final total events: {final_event_count}")
        print(f"Final Google events: {len(final_google_events)}")
        
        # Calculate changes
        new_event_count = final_event_count - initial_event_count
        new_google_events = len(final_google_events) - len(initial_google_events)
        
        print(f"\nNew events added: {new_event_count}")
        print(f"New Google events: {new_google_events}")
        
        # Display Google events
        if final_google_events:
            print("\n--- Google Calendar Events Found ---")
            for i, event in enumerate(final_google_events[:5]):
                print(f"{i+1}. {event['title']}")
                print(f"   Start: {event.get('due_date', 'N/A')}")
                print(f"   Calendar: {event.get('course_name', 'N/A')}")
        
        # Verify data quality
        print("\n--- Verifying Google Event Data Quality ---")
        data_quality_pass = self._verify_google_event_data_quality(final_google_events)
        
        # Verify via API (if endpoint exists)
        print("\n--- Verifying via API ---")
        api_verification_pass = self._verify_google_sync_via_api()
        
        # Verify multiple calendars synced (if user has multiple)
        print("\n--- Verifying Multiple Calendars ---")
        multiple_calendars = self._check_multiple_calendars_synced(final_google_events)
        
        # Determine overall test result
        print("\n" + "="*70)
        print("TEST RESULT DETERMINATION")
        print("="*70 + "\n")
        
        checks = {
            "Google account connected": google_connected,
            "Sync button clicked": sync_result,
            "Sync completion detected": sync_success,
            "Google events appeared": len(final_google_events) > 0,
            "New events added": new_google_events > 0 or len(final_google_events) > 0,
            "Event data quality verified": data_quality_pass,
            "API verification passed": api_verification_pass
        }
        
        # Print results
        for check_name, passed in checks.items():
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"{status}: {check_name}")
        
        all_passed = all(checks.values())
        
        print("\n" + "="*70)
        if all_passed:
            print("OVERALL TEST RESULT: PASS ✓")
            print("Google Calendar sync successful - events synced correctly")
        else:
            print("OVERALL TEST RESULT: FAIL ✗")
            failed_checks = [name for name, passed in checks.items() if not passed]
            print(f"Failed checks: {', '.join(failed_checks)}")
        print("="*70 + "\n")
        
        # Assert for unittest
        self.assertTrue(all_passed, f"Google sync test failed: {failed_checks if not all_passed else ''}")
    
    def _ensure_google_connected(self):
        # First, check if we already have a valid session
        self.driver.get(f"{self.base_url}/auth.html")
        
        # Check localStorage for Google token
        try:
            google_token = self.driver.execute_script(
                "return localStorage.getItem('googleToken');"
            )
            user_id = self.driver.execute_script(
                "return localStorage.getItem('userId');"
            )
            
            if google_token and user_id:
                print(f"✓ Google token found in localStorage")
                print(f"✓ User ID: {user_id}")
                return True
        except Exception as e:
            print(f"Error checking localStorage: {str(e)}")
        
        print("⚠ Google not connected, setting up test user and OAuth...")
        
        try:
            # Step 1: Create a test user
            test_email = f"test_{int(time.time())}@vt.edu"
            test_password = "Test@123"
            
            # Register the test user
            register_data = {
                'email': test_email,
                'password': test_password,
                'canvasUserId': f"test_user_{int(time.time())}"
            }
            
            response = requests.post(
                f"{self.api_url}/auth/register",
                json=register_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                print(f"Failed to create test user: {response.text}")
                return False
                
            user_id = response.json().get('userId')
            if not user_id:
                print("No user ID in registration response")
                return False
                
            # Step 2: Log in the test user
            login_data = {
                'email': test_email,
                'password': test_password
            }
            
            response = requests.post(
                f"{self.api_url}/auth/login",
                json=login_data,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                print(f"Failed to log in test user: {response.text}")
                return False
                
            # Step 3: Simulate Google OAuth flow
            # For testing, we'll use a mock token
            mock_token = {
                'access_token': 'mock_access_token',
                'refresh_token': 'mock_refresh_token',
                'token_type': 'Bearer',
                'expires_in': 3600,
                'scope': 'https://www.googleapis.com/auth/calendar',
                'created': int(time.time())
            }
            
            # Store the mock token in localStorage
            token_str = json.dumps(mock_token).replace("'", "\\'")
            self.driver.execute_script(f"""
                localStorage.setItem('googleToken', '{token_str}');
                localStorage.setItem('userId', '{user_id}');
                return true;
            """)
            
            print(f"✓ Test user created and logged in (ID: {user_id})")
            print("✓ Mock Google OAuth token stored in localStorage")
            return True
            
        except Exception as e:
            print(f"Error setting up test user and OAuth: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def _click_sync_button(self):
        try:
            sync_btn = self.wait.until(
                EC.element_to_be_clickable((By.ID, "syncBtn"))
            )
            
            print("✓ Sync button found and clickable")
            sync_btn.click()
            print("✓ Sync button clicked")
            
            return True
            
        except TimeoutException:
            print("✗ Sync button not found or not clickable")
            return False
        except Exception as e:
            print(f"✗ Error clicking sync button: {str(e)}")
            return False
    
    def _wait_for_google_sync_completion(self):
        try:
            print("Waiting for sync to complete...")
            
            # Wait for sync to complete by checking for the sync button to be re-enabled
            # or for a specific element that indicates sync is complete
            try:
                # Wait for the sync button to be re-enabled (if it was disabled)
                WebDriverWait(self.driver, 15).until(
                    lambda d: not d.find_element(By.ID, "syncBtn").get_attribute("disabled")
                )
                print("✓ Sync button re-enabled, assuming sync completed")
                
                # Also check for a success message if available
                try:
                    notification = WebDriverWait(self.driver, 5).until(
                        EC.presence_of_element_located((By.CLASS_NAME, "notification"))
                    )
                    if notification and "error" not in notification.get_attribute("class"):
                        print(f"✓ Sync notification: {notification.text}")
                    elif notification:
                        print(f"⚠ Sync notification (possible error): {notification.text}")
                except TimeoutException:
                    print("⚠ No sync notification appeared, but sync button was re-enabled")
                
                # Check if events were actually added
                return True
                
            except TimeoutException:
                print("⚠ Sync button did not re-enable within timeout")
                return False
            
        except Exception as e:
            print(f"⚠ Error waiting for sync completion: {str(e)}")
            return False
    
    def _count_calendar_events(self):
        try:
            events_list = self.driver.find_element(By.ID, "eventsList")
            event_items = events_list.find_elements(By.CLASS_NAME, "event-item")
            
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
                if "empty" in item.get_attribute("class"):
                    continue
                
                try:
                    title_elem = item.find_element(By.CLASS_NAME, "event-title")
                    date_elem = item.find_element(By.CLASS_NAME, "event-date")
                    source_elem = item.find_element(By.CLASS_NAME, "event-source")
                    
                    # Calendar name (course_name field)
                    try:
                        course_elem = item.find_element(By.CLASS_NAME, "event-course")
                        calendar_name = course_elem.text
                    except NoSuchElementException:
                        calendar_name = None
                    
                    event = {
                        'title': title_elem.text,
                        'due_date': date_elem.text,
                        'source': source_elem.text,
                        'course_name': calendar_name
                    }
                    events.append(event)
                except Exception as e:
                    print(f"⚠ Error parsing event: {e}")
                    continue
            
        except NoSuchElementException:
            pass
        
        return events
    
    def _verify_google_event_data_quality(self, google_events):
        if not google_events:
            print("⚠ No Google events to verify")
            return False
        
        print(f"Verifying data quality for {len(google_events)} Google events...")
        
        valid_count = 0
        invalid_count = 0
        issues = []
        
        for i, event in enumerate(google_events):
            event_issues = []
            
            # Check title
            has_title = bool(event.get('title', '').strip())
            if not has_title:
                event_issues.append("Missing title")
            
            # Check due_date
            has_due_date = bool(event.get('due_date', '').strip())
            if not has_due_date:
                event_issues.append("Missing due_date")
            
            # Check source
            has_correct_source = event.get('source') == 'Google'
            if not has_correct_source:
                event_issues.append(f"Wrong source: {event.get('source')}")
            
            # Check calendar name (optional but recommended)
            has_calendar = bool(event.get('course_name', '').strip())
            if not has_calendar:
                event_issues.append("Missing calendar name")
            
            is_valid = has_title and has_due_date and has_correct_source
            
            if is_valid:
                valid_count += 1
            else:
                invalid_count += 1
                issues.append(f"Event {i+1}: {', '.join(event_issues)}")
        
        print(f"✓ Valid events: {valid_count}/{len(google_events)}")
        
        if invalid_count > 0:
            print(f"✗ Invalid events: {invalid_count}")
            for issue in issues[:5]:  # Show first 5 issues
                print(f"  - {issue}")
        
        return valid_count > 0 and invalid_count == 0
    
    def _check_multiple_calendars_synced(self, google_events):
        """
        Check if events from multiple Google Calendars were synced.
        
        Args:
            google_events (list): List of Google Calendar events
            
        Returns:
            bool: True if events from multiple calendars are found, False otherwise
        """
        if not google_events:
            print("⚠ No Google events to check for multiple calendars")
            return False
            
        # Get unique calendar names
        calendar_names = set()
        for event in google_events:
            # Try to get calendar name from different possible fields
            calendar_name = event.get('calendar_id') or event.get('course_name') or 'Primary'
            calendar_names.add(calendar_name)
        
        print(f"Found events from {len(calendar_names)} calendar(s): {', '.join(calendar_names) or 'None'}")
        
        # It's a pass if we have events from at least one calendar
        # But we'll consider it a bonus if we have multiple
        multiple_calendars = len(calendar_names) > 1
        
        if multiple_calendars:
            print("✓ Events from multiple calendars found")
        else:
            print("ℹ Only found events from one calendar (this is OK for testing)")
            
        return multiple_calendars
    
    def _verify_google_sync_via_api(self):
        """
        Verification Steps:
        -------------------
        1. Get user_id from localStorage
        2. Call GET /api/calendar/events?userId=X
        3. Filter events where source='Google'
        4. Verify count > 0
        5. Check data structure matches expected format
        """
        try:
            print("\n--- Verifying via API ---")
            
            # Get user ID from localStorage
            user_id = self.driver.execute_script("return localStorage.getItem('userId');")
            if not user_id:
                print("✗ No user ID found in localStorage")
                return False
                
            print(f"Querying API for user {user_id}...")
            
            # Call the API to get events
            response = requests.get(
                f"{self.api_url}/calendar/events",
                params={"userId": user_id},
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                print(f"✗ API request failed with status {response.status_code}")
                return False
                
            data = response.json()
            
            # Check if the response has the expected structure
            if 'events' not in data:
                print("✗ Invalid API response format: 'events' key not found")
                return False
                
            print(f"API returned {len(data['events'])} total events")
            
            # Filter Google events
            google_events = [e for e in data['events'] if e.get('source') == 'Google']
            print(f"Found {len(google_events)} Google events via API")
            
            if not google_events:
                print("⚠ No Google events in API response")
                return False
                
            # Verify event structure
            required_fields = ['title', 'start', 'end', 'source']
            for event in google_events:
                for field in required_fields:
                    if field not in event:
                        print(f"✗ Missing required field '{field}' in event: {event}")
                        return False
            
            print("✓ Google events verified via API")
            
            # Get unique calendar names
            calendar_names = set()
            for event in google_events:
                calendar_name = event.get('course_name') or event.get('calendar_id') or 'Unknown'
                if calendar_name:
                    calendar_names.add(calendar_name)
            
            print(f"\nEvents from {len(calendar_names)} different calendar(s):")
            for name in calendar_names:
                event_count = sum(1 for e in google_events if (e.get('course_name') or e.get('calendar_id') or 'Unknown') == name)
                print(f"  - {name}: {event_count} events")
            
            return True
            
        except Exception as e:
            print(f"✗ API verification failed: {str(e)}")
            import traceback
            traceback.print_exc()
            return False


def run_comprehensive_google_sync_test():
    # Create test suite
    suite = unittest.TestLoader().loadTestsFromTestCase(GoogleCalendarSyncTest)

    # Run with verbose output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)

    # Print summary
    print("\n" + "="*70)
    print("GOOGLE CALENDAR SYNC TEST SUMMARY")
    print("="*70)
    print(f"Tests run: {result.testsRun}")
    print(f"Successes: {result.testsRun - len(result.failures) - len(result.errors)}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped)}")

    if result.skipped:
        print("\nSkipped Tests:")
        for test, reason in result.skipped:
            print(f"  {test}: {reason}")
    
    # Print final separator
    print("="*70 + "\n")
    
    # Return whether all tests were successful
    return result.wasSuccessful()

# Main execution block
if __name__ == "__main__":
    success = run_comprehensive_google_sync_test()
    exit(0 if success else 1)